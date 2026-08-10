"""L0 のユニットテスト。

公式 ollama クライアントをフェイクに差し替え、L0 が「接続を理想化し、
中身は関知しない」――吸収すべき失敗はリトライ／自動 pull で吸収し、
吸収し切れない失敗は 4 型のエラーに畳んで上位へ渡す――ことを検証する。
実サーバは使わない（実接続検証は test_l0_live.py）。
"""

import httpx
import ollama
import pytest

from mu.l0 import (
    OllamaInterface,
    Unreachable,
    ModelUnavailable,
    ResourceExhausted,
    BadRequest,
)


class CountingSleep:
    """time.sleep の差し替え。眠らずに呼ばれた回数だけ数える。"""

    def __init__(self):
        self.calls = 0

    def __call__(self, _delay):
        self.calls += 1


class FakeClient:
    """呼ばれるたびに、あらかじめ積んだ「効果」を 1 つずつ消費する。

    効果が Exception なら raise、そうでなければ return する。
    """

    def __init__(self, chat=None, pull=None, show=None, list_=None):
        self._chat = list(chat or [])
        self._pull = list(pull or [])
        self._show = list(show or [])
        self._list = list(list_ or [])
        self.chat_calls = 0
        self.pull_calls = 0
        self.show_calls = 0
        self.list_calls = 0

    def chat(self, **kwargs):
        self.chat_calls += 1
        return self._consume(self._chat)

    def pull(self, model, **kwargs):
        self.pull_calls += 1
        return self._consume(self._pull)

    def show(self, model, **kwargs):
        self.show_calls += 1
        return self._consume(self._show)

    def list(self):
        self.list_calls += 1
        return self._consume(self._list)

    @staticmethod
    def _consume(effects):
        assert effects, "フェイクに積んだ効果が尽きた（想定より多く呼ばれた）"
        eff = effects.pop(0)
        if isinstance(eff, Exception):
            raise eff
        return eff


def make(client, **kw):
    kw.setdefault("sleep", CountingSleep())
    kw.setdefault("base_delay", 0.0)
    return OllamaInterface(client=client, **kw)


# --- 中身には関知しない（成功はそのまま通す） ---

def test_success_is_passed_through_untouched():
    reply = {"message": {"content": "hi"}}
    c = FakeClient(chat=[reply])
    l0 = make(c)
    assert l0.chat("m", [{"role": "user", "content": "yo"}]) is reply
    assert c.chat_calls == 1


def test_weird_content_is_not_an_error():
    # 拒否・壊れた tool_calls などの「中身」の問題は L0 の関知外。そのまま返す。
    reply = {"message": {"content": "I won't", "tool_calls": "garbage"}}
    c = FakeClient(chat=[reply])
    assert make(c).chat("m", []) is reply


# --- 接続断（ConnectionError） ---

def test_connection_error_recovers_by_retry():
    reply = {"ok": 1}
    c = FakeClient(chat=[ConnectionError("down"), reply])
    sleep = CountingSleep()
    assert make(c, sleep=sleep).chat("m", []) is reply
    assert c.chat_calls == 2
    assert sleep.calls == 1


def test_connection_error_exhausted_becomes_unreachable():
    c = FakeClient(chat=[ConnectionError("down")] * 10)
    sleep = CountingSleep()
    with pytest.raises(Unreachable):
        make(c, sleep=sleep, max_retries=2).chat("m", [])
    assert c.chat_calls == 3  # 初回 + リトライ 2
    assert sleep.calls == 2


# --- タイムアウト／ストリーム切断（httpx.TransportError 系） ---

def test_read_timeout_is_absorbed():
    reply = {"ok": 1}
    c = FakeClient(chat=[httpx.ReadTimeout("slow"), reply])
    assert make(c).chat("m", []) is reply
    assert c.chat_calls == 2


def test_stream_cut_is_absorbed():
    reply = {"ok": 1}
    c = FakeClient(chat=[httpx.RemoteProtocolError("cut"), reply])
    assert make(c).chat("m", []) is reply


# --- モデル未取得（404 → 自動 pull → 再試行） ---

def test_model_not_found_triggers_pull_then_succeeds():
    reply = {"ok": 1}
    c = FakeClient(
        chat=[ollama.ResponseError("model 'm' not found", 404), reply],
        pull=[{"status": "success"}],
    )
    assert make(c).chat("m", []) is reply
    assert c.pull_calls == 1
    assert c.chat_calls == 2


def test_pull_failure_becomes_model_unavailable():
    c = FakeClient(
        chat=[ollama.ResponseError("model 'm' not found", 404)],
        pull=[ollama.ResponseError("no such model in registry", 500)],
    )
    with pytest.raises(ModelUnavailable):
        make(c).chat("m", [])
    assert c.pull_calls == 1


def test_pull_connection_blip_is_retried():
    # 数 GB のダウンロード中の一時的な接続断は pull 側でも吸収する。
    reply = {"ok": 1}
    c = FakeClient(
        chat=[ollama.ResponseError("model 'm' not found", 404), reply],
        pull=[ConnectionError("blip"), {"status": "success"}],
    )
    assert make(c).chat("m", []) is reply
    assert c.pull_calls == 2  # 1回目は接続断 → リトライで成功


def test_pull_connection_exhausted_becomes_unreachable():
    c = FakeClient(
        chat=[ollama.ResponseError("model 'm' not found", 404)],
        pull=[ConnectionError("down")] * 10,
    )
    with pytest.raises(Unreachable):
        make(c, max_retries=2).chat("m", [])
    assert c.pull_calls == 3  # 初回 + リトライ 2


# --- 不正リクエスト（4xx / RequestError） → リトライしない ---

def test_bad_request_is_not_retried():
    c = FakeClient(chat=[ollama.ResponseError("invalid options", 400)])
    sleep = CountingSleep()
    with pytest.raises(BadRequest):
        make(c, sleep=sleep).chat("m", [])
    assert c.chat_calls == 1
    assert sleep.calls == 0


def test_request_error_is_bad_request():
    c = FakeClient(chat=[ollama.RequestError("you must provide a model")])
    with pytest.raises(BadRequest):
        make(c).chat("m", [])
    assert c.chat_calls == 1


# --- リトライ可能な 4xx（408 / 429）は BadRequest にしない ---

def test_request_timeout_408_is_retried():
    reply = {"ok": 1}
    c = FakeClient(chat=[ollama.ResponseError("request timeout", 408), reply])
    assert make(c).chat("m", []) is reply
    assert c.chat_calls == 2


def test_rate_limit_429_exhausted_becomes_resource_exhausted():
    c = FakeClient(chat=[ollama.ResponseError("too many requests", 429)] * 10)
    with pytest.raises(ResourceExhausted):
        make(c, max_retries=1).chat("m", [])
    assert c.chat_calls == 2


# --- サーバエラー（5xx） → リトライ → Unreachable ---

def test_server_error_exhausted_becomes_unreachable():
    c = FakeClient(chat=[ollama.ResponseError("internal", 500)] * 10)
    with pytest.raises(Unreachable):
        make(c, max_retries=1).chat("m", [])
    assert c.chat_calls == 2


# --- 資源不足（OOM 風の 5xx） → 限定リトライ → ResourceExhausted ---

def test_out_of_memory_becomes_resource_exhausted():
    c = FakeClient(
        chat=[ollama.ResponseError("model requires more system memory", 500)] * 10
    )
    with pytest.raises(ResourceExhausted):
        make(c, max_retries=1).chat("m", [])
    assert c.chat_calls == 2


# --- 可用性・能力の確認（show / list。allow_pull=False 経路） ---

def test_show_success_is_passed_through():
    info = {"details": {"family": "gemma"}}
    c = FakeClient(show=[info])
    assert make(c).show("m") is info
    assert c.show_calls == 1


def test_show_404_is_model_unavailable_without_pull():
    # show は存在確認であって理想化（自動 pull）の対象ではない。
    c = FakeClient(show=[ollama.ResponseError("model 'm' not found", 404)])
    with pytest.raises(ModelUnavailable):
        make(c).show("m")
    assert c.pull_calls == 0


def test_list_connection_exhausted_becomes_unreachable():
    c = FakeClient(list_=[ConnectionError("down")] * 10)
    with pytest.raises(Unreachable):
        make(c, max_retries=1).list()
    assert c.list_calls == 2


# --- 既定クライアントのタイムアウト（ハングした接続確立・ストールした応答を理想化の内に） ---
#
# かつてここには「read 無制限」を固定するテストがあった（ローカルの長い生成を切らない意図）。
# 021 の実測（cloud ストールで110分の無音ハング・deadline は協調的で救えない）により
# 合意022 で設計転換——read も有限が既定になった。新しい固定は下の 022 節にある。


# --- ストリーミングは v1 未対応: 明示エラーで fail-fast（拡張点は将来の _idealize_stream） ---

def test_chat_streaming_is_rejected_before_touching_network():
    c = FakeClient(chat=[{"ok": 1}])
    with pytest.raises(NotImplementedError):
        make(c).chat("m", [], stream=True)
    assert c.chat_calls == 0  # ネットワークに触れる前に落ちる


def test_generate_streaming_is_rejected_before_touching_network():
    c = FakeClient()  # 効果ゼロ = クライアントが呼ばれたら破綻する
    with pytest.raises(NotImplementedError):
        make(c).generate("m", "hi", stream=True)


# --- 022: read タイムアウトの有限化（無音ハングの根絶） -------------------------
#
# 021 schedule-v2 実測: cloud モデルへの1呼び出しがストールし、走行全体が110分以上の
# 無音ハング。deadline は協調的（タスク境界でしか見ない）で、チャット呼び出しの内側では
# 発火できない——[[cooperative-deadlines-need-bounded-primitives]]。
# read を有限（既定600s・注入可能）にし、ReadTimeout は既存の接続系リトライ梯子が受ける。


def test_default_client_has_finite_read_timeout():
    l0 = OllamaInterface()
    timeout = l0._client._client.timeout
    assert timeout.connect == 5.0
    assert timeout.read == 600.0     # 実測の最長1呼び出し 161.9s に対し約3.7倍の余裕


def test_read_timeout_is_injectable():
    l0 = OllamaInterface(read_timeout=123.0)
    assert l0._client._client.timeout.read == 123.0


def test_read_timeout_none_is_an_explicit_escape_hatch():
    # 特殊なローカル長生成のための明示的な逃げ道。既定は有限に倒す。
    l0 = OllamaInterface(read_timeout=None)
    assert l0._client._client.timeout.read is None


def test_read_timeout_stall_exhausts_into_unreachable():
    # 恒常的なストール: リトライが尽きたら Unreachable（無限に待たない）。
    c = FakeClient(chat=[httpx.ReadTimeout("stall")] * 10)
    with pytest.raises(Unreachable):
        make(c).chat("m", [])
    assert c.chat_calls == 4         # 初回 + max_retries(3)


def test_a_real_stalled_server_fails_in_finite_time():
    # ストールの模擬（正常系テストではこの穴は永遠に見えない）: 接続を受けて
    # 一切応答しない実 TCP サーバに対し、有限時間で Unreachable に畳まれること。
    import socket
    import threading
    import time as _time

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    held = []

    def hold():
        try:
            conn, _ = server.accept()
            held.append(conn)          # 受けたまま何も返さない＝ストール
            conn2, _ = server.accept() # リトライ分も受ける
            held.append(conn2)
        except OSError:
            pass

    t = threading.Thread(target=hold, daemon=True)
    t.start()
    try:
        l0 = OllamaInterface(
            host=f"http://127.0.0.1:{port}", read_timeout=0.5,
            max_retries=1, sleep=lambda s: None,
        )
        started = _time.monotonic()
        with pytest.raises(Unreachable):
            l0.chat("m", [{"role": "user", "content": "hi"}])
        assert _time.monotonic() - started < 10   # 110分でなく数秒で畳まれる
    finally:
        for conn in held:
            conn.close()
        server.close()
