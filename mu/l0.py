"""L0 — Ollama インタフェース層。

mu の最内層。自律性ゼロ。責務はただ一つ:

    上位に「常に安定して応答が返る、理想化された LLM」を見せる。

**接続は理想化する。中身は関知しない。**

- 「応答を得られたか」に関わる失敗（接続断・タイムアウト・ストリーム切断・
  一時的サーバエラー・モデル未取得）は、この層が吸収する（リトライ／自動 pull）。
- 吸収し切れない失敗は、Ollama の生エラーを隠して 4 つの型に畳んで上位へ渡す。
- 「応答の中身」（拒否・崩れ・空・tool_calls 不正）には一切関知せず、そのまま返す。

上位へ見せるエラーは 4 型だけ:
    Unreachable / ModelUnavailable / ResourceExhausted / BadRequest
"""

from __future__ import annotations

import random
import time
from typing import Any, Callable

import httpx
import ollama


# --- 上位へ見せるエラー（4 型だけ） -----------------------------------------

class L0Error(Exception):
    """L0 が上位へ見せる基盤エラーの基底。"""


class Unreachable(L0Error):
    """到達不能（リトライ尽き）。今 LLM が使えない。"""


class ModelUnavailable(L0Error):
    """モデルを用意できない（pull 失敗・レジストリに存在しない 等）。"""


class ResourceExhausted(L0Error):
    """資源不足（メモリ / VRAM 等。限定リトライ後も回復せず）。"""


class BadRequest(L0Error):
    """呼び出し側の不正（リトライしても無駄）。"""


# OOM を 5xx の中から見分けるためのヒント語（生エラー文字列に対する素朴な一致）。
_OOM_HINTS = (
    "memory",
    "out of memory",
    "oom",
    "not enough",
    "insufficient",
    "vram",
    "no space",
)


def _looks_like_oom(message: str) -> bool:
    m = (message or "").lower()
    return any(hint in m for hint in _OOM_HINTS)


def _reject_streaming(kwargs: dict) -> None:
    """L0 v1 はストリーミング未対応。半端に素通りさせず明示的に落とす（fail-fast）。

    対応する際の拡張点（合意ドキュメント 001 参照）:
      A. `_idealize` の例外分類ラダーを共通分類器へ切り出す
      B. イテレータを包む `_idealize_stream` を足す
      C. chat/generate で stream を B へ分岐する
    """
    if kwargs.get("stream"):
        raise NotImplementedError(
            "L0 v1 は stream=True を未対応です。"
            "拡張点: _idealize_stream（A 分類器抽出 / B ストリーム版 / C 分岐）。"
        )


class OllamaInterface:
    """公式 ollama クライアントを包み、理想化を足した L0。

    テスト容易性のため、クライアントと sleep は差し替え可能にしてある。
    """

    def __init__(
        self,
        host: str | None = None,
        *,
        client: Any | None = None,
        connect_timeout: float | None = 5.0,
        max_retries: int = 3,
        base_delay: float = 0.5,
        max_delay: float = 8.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if client is None:
            # connect のみタイムアウトを課す（ハングした接続確立を理想化の内に入れる）。
            # read/write は無制限のまま — ローカル LLM の生成は長く、切ると生成自体を壊す。
            client = ollama.Client(
                host=host, timeout=httpx.Timeout(None, connect=connect_timeout)
            )
        self._client = client
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._sleep = sleep

    # --- 公開: 理想化された推論 --------------------------------------------

    def chat(self, model: str, messages: Any, **kwargs: Any) -> Any:
        _reject_streaming(kwargs)  # 拡張点C: 将来ここで stream を _idealize_stream へ分岐
        return self._idealize(
            model, lambda: self._client.chat(model=model, messages=messages, **kwargs)
        )

    def generate(self, model: str, prompt: str | None = None, **kwargs: Any) -> Any:
        _reject_streaming(kwargs)  # 拡張点C
        if prompt is not None:
            kwargs["prompt"] = prompt
        return self._idealize(
            model, lambda: self._client.generate(model=model, **kwargs)
        )

    # --- 公開: 可用性・能力の確認（上位が使う。pull はしない） --------------

    def show(self, model: str) -> Any:
        return self._idealize(model, lambda: self._client.show(model), allow_pull=False)

    def list(self) -> Any:
        return self._idealize(None, lambda: self._client.list(), allow_pull=False)

    # --- 核: 理想化ループ --------------------------------------------------

    def _idealize(self, model: str | None, call: Callable[[], Any], *, allow_pull: bool = True) -> Any:
        attempt = 0
        pulled = False
        while True:
            try:
                return call()

            # --- 拡張点A: 以下の例外分類ラダーは、ストリーミング対応時に
            #     _idealize_stream と共有できるよう共通分類器へ切り出す ---
            # 接続断（refused / サーバ停止）。ollama が組み込み ConnectionError に畳む。
            except ConnectionError as e:
                attempt = self._retry_or_raise(attempt, Unreachable, str(e))

            # タイムアウト・ストリーム切断・プロトコル異常など transport 層。
            except httpx.TransportError as e:
                attempt = self._retry_or_raise(attempt, Unreachable, repr(e))

            # HTTP エラー応答。status_code で分岐する。
            except ollama.ResponseError as e:
                code = getattr(e, "status_code", -1)
                if code == 404:
                    # モデル未取得 → 一度だけ黙って pull して原呼び出しを再試行。
                    if allow_pull and model and not pulled:
                        self._pull(model)  # 失敗時は ModelUnavailable / Unreachable を送出
                        pulled = True
                        continue
                    raise ModelUnavailable(e.error) from None
                if code == 408:  # Request Timeout: 一時的とみなしリトライ
                    attempt = self._retry_or_raise(attempt, Unreachable, e.error)
                    continue
                if code == 429:  # Too Many Requests: サーバ側の資源逼迫としてリトライ
                    attempt = self._retry_or_raise(attempt, ResourceExhausted, e.error)
                    continue
                if 400 <= code < 500:
                    raise BadRequest(e.error) from None
                # 5xx / 不明(-1) は一時的とみなす。ただし OOM 風は資源不足へ。
                if _looks_like_oom(e.error):
                    attempt = self._retry_or_raise(attempt, ResourceExhausted, e.error)
                else:
                    attempt = self._retry_or_raise(attempt, Unreachable, e.error)

            # リクエスト構築の不正（例: モデル未指定）。呼び出し側のバグ。
            except ollama.RequestError as e:
                raise BadRequest(e.error) from None

    def _pull(self, model: str) -> None:
        # 数 GB のダウンロード中の接続断は現実的に起きる。chat と同じく接続系は
        # リトライで吸収する（レジストリ側の失敗＝ResponseError はリトライしない）。
        attempt = 0
        while True:
            try:
                self._client.pull(model)
                return
            except ConnectionError as e:
                attempt = self._retry_or_raise(attempt, Unreachable, str(e))
            except httpx.TransportError as e:
                attempt = self._retry_or_raise(attempt, Unreachable, repr(e))
            except (ollama.ResponseError, ollama.RequestError) as e:
                raise ModelUnavailable(getattr(e, "error", str(e))) from None

    def _retry_or_raise(self, attempt: int, exc_type: type[L0Error], message: str) -> int:
        if attempt >= self.max_retries:
            raise exc_type(message) from None
        delay = min(self.max_delay, self.base_delay * (2 ** attempt))
        delay += random.uniform(0.0, delay)  # ジッタ
        self._sleep(delay)
        return attempt + 1
