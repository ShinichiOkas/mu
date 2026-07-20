"""L3（大域的 Plan / 複雑タスクの完遂）のユニットテスト。

Plan/分析/再計画/全体判定（L0 の構造化出力）と、各単位の完遂（L2）を
フェイクに差し替え、「Plan→承認(HITL)→単位をL2で完遂→失敗なら分析＆再計画」
の機構を検証する。実サーバは使わない。
"""

import json
import types

from mu.l3 import Orchestrator


class FakeL0:
    """構造化 chat の代役。用意した dict を順に JSON で返す（尽きたら直近を繰り返す）。"""

    def __init__(self, responses):
        self._responses = list(responses)
        self._last = {}
        self.calls = []

    def chat(self, model, messages, **kwargs):
        if self._responses:
            self._last = self._responses.pop(0)
        self.calls.append({"format": kwargs.get("format"), "messages": messages})
        return types.SimpleNamespace(
            message=types.SimpleNamespace(content=json.dumps(self._last))
        )


class FakeL2:
    """単位実行（D）の代役。run ごとに pass/fail を返す。goal を記録。"""

    def __init__(self, results):
        self._results = list(results)
        self.calls = []
        self.systems = []

    def run(self, model, goal, tools, max_rounds=6, l1_max=10, system=None):
        self.calls.append(goal)
        self.systems.append(system)
        passed = self._results.pop(0) if self._results else True
        return ([{"role": "user", "content": goal}], passed)


def plan(*units):
    return {"units": [{"task": t, "file": f, "criterion": c} for (t, f, c) in units]}


PLAN2 = plan(
    ("write tests", "test_calc.py", "tests exist"),
    ("implement", "calc.py", "tests pass"),
)
PLAN1 = plan(("implement", "calc.py", "tests pass"))
OVERALL_OK = {"passed": True, "reason": "all deliverables present"}
ANALYZE = {"reason": "too large", "suggestion": "split"}


def make(l0_responses, l2_results):
    return Orchestrator(FakeL0(l0_responses), l2=FakeL2(l2_results))


def test_happy_path_all_units_pass():
    agent = make([PLAN2, OVERALL_OK], [True, True])
    result = agent.run("m", "build calc", [])
    assert result["done"] is True
    assert agent._l2.calls and len(agent._l2.calls) == 2  # 2 単位を実行
    assert all(u["done"] for u in result["units"])


def test_unit_failure_triggers_analyze_and_replan():
    # 1単位: 1回失敗 → 分析＋再計画（同じ単位）→ 2回目成功 → 全体OK
    agent = make([PLAN1, ANALYZE, PLAN1, OVERALL_OK], [False, True])
    result = agent.run("m", "build calc", [])
    assert result["done"] is True
    assert len(agent._l2.calls) == 2  # 失敗→再実行


def test_unit_goal_includes_file_and_criterion():
    agent = make([PLAN1, OVERALL_OK], [True])
    agent.run("m", "build calc", [])
    goal_sent = agent._l2.calls[0]
    assert "calc.py" in goal_sent
    assert "tests pass" in goal_sent


def test_run_forwards_system_preamble_to_l2():
    # 環境グラウンディングは呼び出し側の責務。L3 は system をそのまま L2 へ通す
    # （L3 自身は環境を知らない・opaque に転送するだけ）。
    agent = make([PLAN1, OVERALL_OK], [True])
    agent.run("m", "build calc", [], system="ENV-PREAMBLE-XYZ")
    assert agent._l2.systems[0] == "ENV-PREAMBLE-XYZ"


def test_approve_called_for_plan_and_replan():
    seen = []

    def approve(units):
        seen.append([u["file"] for u in units])
        return units

    agent = make([PLAN1, ANALYZE, PLAN1, OVERALL_OK], [False, True])
    agent.run("m", "build calc", [], approve=approve)
    assert len(seen) == 2  # Plan と 再計画 の2回、HITL 承認が走る


def test_approve_can_edit_plan():
    # 承認者が単位を1つに削る → L3 はそれに従う
    def approve(units):
        return units[:1]

    agent = make([PLAN2, OVERALL_OK], [True])
    result = agent.run("m", "build calc", [], approve=approve)
    assert len(result["units"]) == 1
    assert len(agent._l2.calls) == 1


def test_done_units_not_reexecuted_after_replan():
    # 2単位: 1つ目成功, 2つ目失敗→再計画(同じ2単位)。1つ目は done を維持し再実行しない。
    agent = make([PLAN2, ANALYZE, PLAN2, OVERALL_OK], [True, False, True])
    result = agent.run("m", "build calc", [])
    # test_calc.py は最初に成功→以降呼ばれない。calc.py は失敗→再実行で計2回。
    calc_calls = [g for g in agent._l2.calls if "calc.py" in g and "test_calc.py" not in g]
    testfile_calls = [g for g in agent._l2.calls if "test_calc.py" in g]
    assert len(testfile_calls) == 1
    assert result["done"] is True


def test_max_rounds_returns_not_done():
    agent = make([PLAN1, ANALYZE, PLAN1], [False, False, False])
    result = agent.run("m", "build calc", [], max_rounds=3)
    assert result["done"] is False


def test_final_overall_runs_after_max_rounds_when_all_done():
    # max_rounds を単位実行で使い切っても、全単位 done なら最終の全体判定を必ず1回行う。
    agent = make([PLAN1, OVERALL_OK], [True])
    result = agent.run("m", "build calc", [], max_rounds=1)
    assert result["done"] is True
    assert len(agent._l0.calls) == 2  # plan + 最終 overall


def test_final_overall_failure_after_max_rounds_returns_not_done():
    agent = make([PLAN1, {"passed": False, "reason": "goal needs more"}], [True])
    result = agent.run("m", "build calc", [], max_rounds=1)
    assert result["done"] is False


def test_overall_failure_triggers_replan_and_continues():
    # 全単位 done → overall 不合格 → 再計画（不足単位を追加）→ 完遂、の else 分岐。
    agent = make(
        [PLAN1, {"passed": False, "reason": "tests missing"}, PLAN2, OVERALL_OK],
        [True, True],
    )
    result = agent.run("m", "build calc", [])
    assert result["done"] is True
    # calc.py は done を引き継ぎ再実行されない。追加された test_calc.py だけ実行される。
    assert len(agent._l2.calls) == 2
    assert any("test_calc.py" in g for g in agent._l2.calls)


def test_empty_plan_does_not_crash_and_executes_nothing():
    # Plan が空（units:[] や壊れた {}）でも落ちず、L2 を一度も呼ばずに未達で返る。
    agent = make(
        [{"units": []}, {"passed": False, "reason": "no deliverables"}, {"units": []}],
        [],
    )
    result = agent.run("m", "build calc", [], max_rounds=2)
    assert result["done"] is False
    assert agent._l2.calls == []


def test_result_includes_rounds_consumed():
    # 1周=1単位実行 or 1全体判定。上限到達の判別（done=False かつ rounds==max_rounds）用。
    agent = make([PLAN2, OVERALL_OK], [True, True])
    result = agent.run("m", "build calc", [])
    assert result["rounds"] == 3  # 2単位 + 全体判定1回
