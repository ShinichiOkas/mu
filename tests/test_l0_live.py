"""L0 の実接続スモークテスト。

方針スキル「バックエンドをモックするなら実接続も検証する」に従い、
ユニットテスト（フェイク）とは別に、実際に動いている Ollama へ最小の
往復を 1 回行って L0 が本物相手に機能することを確かめる。

サーバが起動していなければ丸ごとスキップする（CI 等でも壊さない）。
実行:  pytest -m live
"""

import pytest

from mu.l0 import OllamaInterface, L0Error

pytestmark = pytest.mark.live

# スモークに使う小型ローカルモデルの候補（先頭から、存在するものを使う）。
SMALL_MODELS = ["gemma3:1b", "qwen3.5:0.8b", "qwen3.5:2b", "qwen3.5:4b"]


def _model_name(m):
    return getattr(m, "model", None) or getattr(m, "name", None)


@pytest.fixture(scope="module")
def l0():
    iface = OllamaInterface()
    try:
        iface.list()
    except Exception as e:  # noqa: BLE001 — 到達不能なら理由を添えてスキップ
        pytest.skip(f"Ollama サーバに接続できないためスキップ: {e!r}")
    return iface


@pytest.fixture(scope="module")
def model(l0):
    present = {_model_name(m) for m in l0.list().models}
    for cand in SMALL_MODELS:
        if cand in present:
            return cand
    pytest.skip(f"小型ローカルモデルが見つからない（present={sorted(present)}）")


def test_live_chat_returns_content(l0, model):
    resp = l0.chat(
        model,
        [{"role": "user", "content": "Reply with exactly one word: pong"}],
        options={"num_predict": 8},
    )
    # 「応答が得られたか」だけを見る。中身の正しさは L0 の関知外。
    assert resp.message.content.strip() != ""


def test_live_unknown_model_surfaces_l0_error(l0):
    # 存在しないモデル → 404 → 自動 pull 試行 → 解決不能 → L0 の型付きエラー。
    with pytest.raises(L0Error):
        l0.chat(
            "mu-no-such-model-zzz:0.0",
            [{"role": "user", "content": "hi"}],
        )
