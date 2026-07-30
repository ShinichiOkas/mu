"""L3（大域的 Plan / 複雑タスクの完遂）のユニットテスト。

Plan/分析/再計画（L0 の構造化出力）と、各単位の完遂（L2）をフェイクに
差し替え、「Plan→承認→単位をL2で完遂→失敗なら分析＆再計画」の機構を
検証する。実サーバは使わない。

完了判定は機械的照合（全単位 done。空の計画は未達）。「仕様を網羅したか」の
推測判定（旧 overall。機序④＝幻覚の温床）は L4 の目的判定へ移した（合意005）。
"""

import json
import types

from mu.l3 import Orchestrator, _carry_done


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
ANALYZE = {"reason": "too large", "suggestion": "split"}


def make(l0_responses, l2_results):
    return Orchestrator(FakeL0(l0_responses), l2=FakeL2(l2_results))


def test_happy_path_all_units_pass():
    agent = make([PLAN2], [True, True])
    result = agent.run("m", "build calc", [])
    assert result["done"] is True
    assert agent._l2.calls and len(agent._l2.calls) == 2  # 2 単位を実行
    assert all(u["done"] for u in result["units"])


def test_unit_failure_triggers_analyze_and_replan():
    # 1単位: 1回失敗 → 分析＋再計画（同じ単位）→ 2回目成功 → 完遂
    agent = make([PLAN1, ANALYZE, PLAN1], [False, True])
    result = agent.run("m", "build calc", [])
    assert result["done"] is True
    assert len(agent._l2.calls) == 2  # 失敗→再実行


def test_unit_goal_includes_file_and_criterion():
    agent = make([PLAN1], [True])
    agent.run("m", "build calc", [])
    goal_sent = agent._l2.calls[0]
    assert "calc.py" in goal_sent
    assert "tests pass" in goal_sent


def test_run_forwards_system_preamble_to_l2():
    # 環境グラウンディングは呼び出し側の責務。L3 は system をそのまま L2 へ通す
    # （L3 自身は環境を知らない・opaque に転送するだけ）。
    agent = make([PLAN1], [True])
    agent.run("m", "build calc", [], system="ENV-PREAMBLE-XYZ")
    assert agent._l2.systems[0] == "ENV-PREAMBLE-XYZ"


def test_approve_called_for_plan_and_replan():
    seen = []

    def approve(units):
        seen.append([u["file"] for u in units])
        return units

    agent = make([PLAN1, ANALYZE, PLAN1], [False, True])
    agent.run("m", "build calc", [], approve=approve)
    assert len(seen) == 2  # Plan と 再計画 の2回、承認スロットが走る


def test_approve_can_edit_plan():
    # 承認者が単位を1つに削る → L3 はそれに従う
    def approve(units):
        return units[:1]

    agent = make([PLAN2], [True])
    result = agent.run("m", "build calc", [], approve=approve)
    assert len(result["units"]) == 1
    assert len(agent._l2.calls) == 1


def test_done_units_not_reexecuted_after_replan():
    # 2単位: 1つ目成功, 2つ目失敗→再計画(同じ2単位)。1つ目は done を維持し再実行しない。
    agent = make([PLAN2, ANALYZE, PLAN2], [True, False, True])
    result = agent.run("m", "build calc", [])
    # test_calc.py は最初に成功→以降呼ばれない。calc.py は失敗→再実行で計2回。
    testfile_calls = [g for g in agent._l2.calls if "test_calc.py" in g]
    assert len(testfile_calls) == 1
    assert result["done"] is True


def test_max_rounds_returns_not_done():
    agent = make([PLAN1, ANALYZE, PLAN1], [False, False, False])
    result = agent.run("m", "build calc", [], max_rounds=3)
    assert result["done"] is False


def test_completion_is_mechanical_no_llm_judgment():
    # 完了判定は照合（全単位 done）であり、LLM を呼ばない。
    # 「仕様を網羅したか」の推測判定（旧 overall）は L4 の目的判定へ移した。
    agent = make([PLAN2], [True, True])
    result = agent.run("m", "build calc", [])
    assert result["done"] is True
    assert len(agent._l0.calls) == 1  # plan のみ（overall の LLM 呼び出しは無い）


def test_overall_log_event_reports_mechanical_verdict():
    events = []
    agent = make([PLAN1], [True])
    agent.run("m", "build calc", [], log=events.append)
    overalls = [e for e in events if e[0] == "overall"]
    assert len(overalls) == 1
    assert overalls[0][1]["passed"] is True


def test_empty_plan_is_not_done():
    # Plan が空（units:[] や壊れた {}）でも落ちず、L2 を呼ばず未達で返る。
    # 機械的照合で「空の計画＝全単位 done」と誤読しない（空 done の穴を塞ぐ）。
    agent = make([{"units": []}], [])
    result = agent.run("m", "build calc", [], max_rounds=2)
    assert result["done"] is False
    assert agent._l2.calls == []


def test_result_includes_rounds_consumed():
    # 1周=1単位実行（失敗周は分析＋再計画を含む）。上限到達の判別用。
    agent = make([PLAN2], [True, True])
    result = agent.run("m", "build calc", [])
    assert result["rounds"] == 2  # 2単位。完了照合は周を消費しない


# --- _carry_done の同一ファイル穴（F1-g で偽・完遂として実発火）---

PLAN_SAME3 = plan(
    ("core logic", "todo.py", "core functions exist"),
    ("persistence and undo", "todo.py", "json save/load works"),
    ("cli and selftest", "todo.py", "selftest passes 12+"),
)


def test_replan_with_duplicate_files_does_not_fake_done():
    # 同一ファイル3単位のうち1つが失敗し、再計画が同じ3単位を返しても、
    # 失敗した単位が done に化けて完了照合へ直行（偽・完遂）してはならない。
    agent = make(
        [PLAN_SAME3, ANALYZE, PLAN_SAME3],
        [True, True, False],  # 3単位目だけ失敗。以降（再実行）はデフォルト True
    )
    result = agent.run("m", "build todo app", [])
    # 安全側: 重複 file の done は引き継がず再実行される（L2 呼び出しが3回を超える）。
    assert len(agent._l2.calls) > 3
    assert result["done"] is True  # 再実行の末の本物の完遂


def test_carry_done_skips_files_duplicated_in_old_plan():
    # 旧計画内で file が重複していたら、単位の同一性が壊れているので引き継がない。
    old = [
        {"task": "a", "file": "app.py", "done": True},
        {"task": "b", "file": "app.py", "done": True},
        {"task": "c", "file": "app.py"},  # 失敗した単位（未 done）
        {"task": "t", "file": "test.py", "done": True},
    ]
    new = [
        {"task": "a2", "file": "app.py"},
        {"task": "b2", "file": "app.py"},
        {"task": "c2", "file": "app.py"},
        {"task": "t2", "file": "test.py"},
    ]
    out = _carry_done(old, new)
    assert [bool(u.get("done")) for u in out] == [False, False, False, True]


def test_carry_done_skips_files_duplicated_in_new_plan():
    # 新計画側で file が重複していても、まとめて done 化させない（過剰マーク防止）。
    old = [{"task": "a", "file": "app.py", "done": True}]
    new = [{"task": "a1", "file": "app.py"}, {"task": "a2", "file": "app.py"}]
    out = _carry_done(old, new)
    assert all(not u.get("done") for u in out)
