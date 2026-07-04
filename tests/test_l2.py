"""L2（PDCA / Reflect ループ）のユニットテスト。

D（L1）と Reflect（L0 の構造化出力）をフェイクに差し替え、
「D → Reflect → 合格で終了／未達は next を再投入して継続」を検証する。
実サーバは使わない。
"""

import json
import types

from mu.l2 import Agent


class FakeL1:
    """D の代役。呼ばれるたびに assistant メッセージを1つ積む。"""

    def __init__(self, outputs=None):
        self._outputs = list(outputs or [])
        self.calls = 0

    def run(self, model, messages, tools, max_rounds=32):
        self.calls += 1
        content = self._outputs.pop(0) if self._outputs else "did something"
        messages.append({"role": "assistant", "content": content})
        return messages


class FakeReflectL0:
    """Reflect の代役。chat() で用意した verdict(JSON) を順に返す。"""

    def __init__(self, verdicts):
        self._verdicts = list(verdicts)
        self.calls = []

    def chat(self, model, messages, **kwargs):
        self.calls.append({"messages": messages, "format": kwargs.get("format")})
        v = self._verdicts.pop(0)
        content = v if isinstance(v, str) else json.dumps(v)
        return types.SimpleNamespace(message=types.SimpleNamespace(content=content))


def verdict(passed, reason="", nxt=""):
    return {"passed": passed, "reason": reason, "next": nxt}


def make(l1_outputs, verdicts):
    return Agent(FakeReflectL0(verdicts), l1=FakeL1(l1_outputs))


def test_passes_first_round():
    agent = make(["done"], [verdict(True, "achieved")])
    messages, passed = agent.run("m", "do the thing", [])
    assert passed is True
    assert agent._l1.calls == 1
    assert len(agent._l0.calls) == 1


def test_loops_until_pass():
    agent = make(["attempt1", "attempt2"], [verdict(False, "not yet", "finish X"), verdict(True)])
    messages, passed = agent.run("m", "goal", [], max_rounds=5)
    assert passed is True
    assert agent._l1.calls == 2  # D は2周


def test_reflect_next_is_reinjected_as_user_feedback():
    # フィードバックは user ロールで戻る（L1 が読む）。目印付きで transcript からは除外される。
    agent = make(["a", "b"], [verdict(False, "missing", "write the file"), verdict(True)])
    messages, _ = agent.run("m", "goal", [])
    assert any(
        m.get("role") == "user" and "write the file" in m.get("content", "")
        for m in messages
    )


def test_hits_max_rounds_returns_false():
    agent = make(["x", "x", "x"], [verdict(False, "no"), verdict(False, "no"), verdict(False, "no")])
    messages, passed = agent.run("m", "goal", [], max_rounds=3)
    assert passed is False
    assert agent._l1.calls == 3


def test_unparseable_verdict_is_not_passed():
    # JSON でない Reflect 応答でも落ちず、未達扱いでループ上限まで回る。
    agent = make(["x"], ["this is not json"])
    messages, passed = agent.run("m", "goal", [], max_rounds=1)
    assert passed is False


def test_system_preamble_is_prepended():
    agent = make(["x"], [verdict(True)])
    messages, _ = agent.run("m", "goal", [], system="ENV-XYZ")
    assert messages[0]["role"] == "system"
    assert "ENV-XYZ" in messages[0]["content"]


def test_goal_becomes_first_user_message():
    agent = make(["x"], [verdict(True)])
    messages, _ = agent.run("m", "summarize the repo", [])
    assert any(m.get("role") == "user" and m["content"] == "summarize the repo" for m in messages)


def test_reflect_uses_structured_output_format():
    agent = make(["x"], [verdict(True)])
    agent.run("m", "goal", [])
    assert agent._l0.calls[0]["format"] is not None  # format(スキーマ) を渡している
