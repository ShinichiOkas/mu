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

    def __init__(self, chat=None, pull=None):
        self._chat = list(chat or [])
        self._pull = list(pull or [])
        self.chat_calls = 0
        self.pull_calls = 0

    def chat(self, **kwargs):
        self.chat_calls += 1
        return self._consume(self._chat)

    def pull(self, model, **kwargs):
        self.pull_calls += 1
        return self._consume(self._pull)

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
