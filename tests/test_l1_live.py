"""L1 の実接続スモーク。

tool 対応モデルに対し、明示的にツールを促すと、実際にツールが実行され、
その結果を踏まえた最終回答が返る——というループ全体を本物で確かめる。
サーバや tool 対応モデルが無ければスキップする。実行: pytest -m live
"""

import pytest

from mu.l0 import OllamaInterface
from mu.l1 import ToolLoop

pytestmark = pytest.mark.live

TOOL_MODELS = ["qwen3.5:9b", "gemma4:12b", "qwen3.5:4b", "qwen2.5-coder:7b"]


def multiply(a: float, b: float) -> float:
    """2 つの数を掛ける。"""
    return a * b


def _model_name(m):
    return getattr(m, "model", None) or getattr(m, "name", None)


@pytest.fixture(scope="module")
def l0():
    iface = OllamaInterface()
    try:
        iface.list()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"Ollama 未接続: {e!r}")
    return iface


@pytest.fixture(scope="module")
def tool_model(l0):
    present = {_model_name(m) for m in l0.list().models}
    for cand in TOOL_MODELS:
        if cand in present:
            return cand
    pytest.skip(f"tool 対応モデルが見つからない（present={sorted(present)}）")


def test_live_tool_is_called_and_result_used(l0, tool_model):
    l1 = ToolLoop(l0)
    messages = [{"role": "user", "content": "Use the multiply tool to compute 23 * 47."}]
    messages = l1.run(tool_model, messages, [(multiply, "multiply(a, b): 2 つの数を掛ける")])

    tool_msgs = [m for m in messages if m.get("role") == "tool"]
    assert any(
        t["tool_name"] == "multiply" and float(t["content"]) == 1081.0 for t in tool_msgs
    ), f"multiply が期待どおり実行されていない: {messages}"
    # 最後は tool_call の無い、中身のある assistant 応答
    assert messages[-1]["role"] == "assistant" and messages[-1]["content"].strip()
