"""L4（進行の層 / PjM）のユニットテスト。

L5 を通さず **Manager 単体**の契約を検証する（合意009 で L4 は SPEC を受け取る層になった）:

- SPEC → プロセス → 役割を着せた L3 の逐次実行 → 決定論 check ＋ verdict の機械読み
- **rerun / replan は自分で回し、respec / escalate は上へ返す**（判断は外へ、実行は内で）
- 予算は自分で持つ（尽きたら escalate として上へ返す）
"""

import json
import types

import tools
from mu.l4 import Manager


class FakeL0:
    """構造化 chat の代役。dict は JSON で返す。"""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def chat(self, model, messages, **kwargs):
        self.calls.append({"format": kwargs.get("format"), "messages": messages})
        assert self._responses, "フェイク L0 の応答が尽きた"
        r = self._responses.pop(0)
        return types.SimpleNamespace(
            message=types.SimpleNamespace(content=r if isinstance(r, str) else json.dumps(r))
        )


class FakeL3:
    def __init__(self, results=None):
        self._results = list(results or [])
        self.calls = []

    def run(self, model, goal, tools, **kwargs):
        self.calls.append({"model": model, "goal": goal, "tools": tools, "kwargs": kwargs})
        r = self._results.pop(0) if self._results else {"done": True}
        for path, content in r.get("writes", []):
            from pathlib import Path
            Path(path).write_text(content, encoding="utf-8")
        return {"units": [], "done": r.get("done", True), "rounds": 1}


SPEC = {
    "definitions": [], "criteria": [{"text": "result.csv がある", "run": "", "expect": ""}],
    "spec": "result.csv を作る", "feasible": True, "conflicts": [],
}
PROCESS2 = {"tasks": [
    {"role": "implementer", "task": "実装する", "file": "result.csv", "criterion": "出力する"},
    {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ITEM 行"},
]}
# 017: 判定書は受入基準ごとの二値。総合判定（ACHIEVED）は書かせず、集約はコードが行う。
# SPEC の受入基準は1件なので ITEM 1 のみ。
VERDICT_YES = "ITEM 1: PASS — result.csv を確認した\nGAP:\n"
VERDICT_NO = "ITEM 1: FAIL — 列が欠けている\nGAP: 列が足りない\n"
ROLES = {"implementer": "IMPL-MARKER", "qa": "QA-MARKER", "pjm": "PJM-MARKER"}

ok2 = lambda: [{"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_YES)]}]


def make(responses, l3_results=None):
    return Manager(FakeL0(responses), l3=FakeL3(l3_results))


def run(mgr, tmp_path, monkeypatch, **kw):
    monkeypatch.chdir(tmp_path)
    kw.setdefault("roles", ROLES)
    return mgr.run("m", SPEC, [], **kw)


def test_done_when_verdict_yes_and_checks_pass(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "done"
    assert out["ok"] is True
    assert out["verdict"]["achieved"] == "yes"
    assert out["rounds"] == 1
    assert len(mgr._l3.calls) == 2


def test_rerun_is_handled_inside_this_layer(tmp_path, monkeypatch):
    # 自分の職掌で直せる失敗は上へ返さない（判断は外へ、実行は内で）。
    decide = {"action": "rerun", "invalidate": ["result.csv"], "reason": "出力不良"}
    mgr = make([PROCESS2, decide], [
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_NO)]},
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
    ])
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "done"
    assert out["rounds"] == 2
    assert len(mgr._l3.calls) == 4


def test_rerun_hands_the_failed_check_facts_to_the_re_executed_task(tmp_path, monkeypatch):
    # 014: 理由を添えずに再実行させると、実行者は成果物でなく検査器を直しにいく（013 実走）。
    # 再実行されるタスクの goal に「コードが実行した事実」が載ることを検査する。
    spec = {
        "definitions": [], "spec": "result.csv を作る", "feasible": True, "conflicts": [],
        "criteria": [{"text": "マーカーが出る", "run": "echo NOPE", "expect": "MARKER"}],
    }
    decide = {"action": "rerun", "invalidate": ["result.csv"], "reason": "出力不良"}
    give_up = {"action": "escalate", "invalidate": [], "reason": "直らない"}
    # 検査（echo NOPE）は毎周落ちるので、2周目のあと escalate で終える。
    mgr = make([PROCESS2, decide, give_up], [
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
    ])
    monkeypatch.chdir(tmp_path)
    mgr.run("m", spec, list(tools.TOOLS), roles=ROLES)
    first_goal, rerun_goal = mgr._l3.calls[0]["goal"], mgr._l3.calls[2]["goal"]
    assert "前回の失敗" not in first_goal          # 初回は失敗が無い
    assert "前回の失敗" in rerun_goal              # 再実行では事実が届く
    assert "echo NOPE" in rerun_goal               # 実行された検査コマンド
    assert "検査スクリプトを書き換えて" in rerun_goal  # 検査器を直す方向への流出を止める


def test_criteria_without_a_command_are_reported_as_unverified(tmp_path, monkeypatch):
    # 015: run が空の基準は「検査されたのか、項目が無かったのか」が外から区別できなかった。
    # 隠れた合格を無くすため、未検査として結果に出す（完遂判定は変えない）。
    spec = {
        "definitions": [], "spec": "report.md を作る", "feasible": True, "conflicts": [],
        "criteria": [
            {"text": "ファイルがある", "run": "echo MARKER", "expect": "MARKER"},
            {"text": "洞察が妥当であること", "run": "", "expect": ""},
        ],
    }
    # 受入基準が2件なので判定書も2項目書く（欠番は UNCERTAIN 扱いになる）。
    two = "ITEM 1: PASS — ある\nITEM 2: PASS — 妥当\n"
    mgr = make([PROCESS2], [{"done": True}, {"done": True, "writes": [("verdict.md", two)]}])
    monkeypatch.chdir(tmp_path)
    out = mgr.run("m", spec, list(tools.TOOLS), roles=ROLES)
    kinds = {c["text"]: c["kind"] for c in out["checks"]}
    assert kinds["ファイルがある"] == "machine"
    assert kinds["洞察が妥当であること"] == "unverified"


def test_unverified_criteria_do_not_block_completion(tmp_path, monkeypatch):
    # 未検査があっても達成は返す（明示して達成可＝合意015 ③）。床は動かさない。
    spec = {
        "definitions": [], "spec": "report.md を作る", "feasible": True, "conflicts": [],
        "criteria": [{"text": "洞察が妥当であること", "run": "", "expect": ""}],
    }
    mgr = make([PROCESS2], ok2())
    monkeypatch.chdir(tmp_path)
    out = mgr.run("m", spec, list(tools.TOOLS), roles=ROLES)
    assert out["outcome"] == "done"
    assert out["ok"] is True
    assert [c["kind"] for c in out["checks"]] == ["unverified"]


def test_guard_stops_the_round_when_a_protected_input_is_broken(tmp_path, monkeypatch):
    # 016: 入力が壊れた後の作業はすべて偽の前提の上に乗る。015 では壊れたまま進み、
    # 実データでない「Widget B」の報告書ができた（完走していたら偽・完遂）。
    broken = [{"path": "inventory.csv", "status": "modified"}]
    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch, guard=lambda: broken)
    assert out["outcome"] == "escalate"
    assert "inventory.csv" in out["reason"]
    assert mgr._l3.calls == []      # 壊れた前提の上で1タスクも走らせない


def test_guard_that_reports_nothing_does_not_interfere(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch, guard=lambda: [])
    assert out["outcome"] == "done"


def test_guard_is_checked_every_round_not_only_at_the_end(tmp_path, monkeypatch):
    # 015 で判明: 走り切らないと検出報告が出ない。周ごと・タスクごとに見る（018 で粒度を強化。
    # 2回目の検査＝1周目のタスク1の前で止まる——1周待たない）。
    seen = {"n": 0}

    def guard():
        seen["n"] += 1
        return [{"path": "input.csv", "status": "missing"}] if seen["n"] > 1 else []

    decide = {"action": "rerun", "invalidate": ["result.csv"], "reason": "やり直し"}
    mgr = make([PROCESS2, decide], [
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_NO)]},
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
    ])
    out = run(mgr, tmp_path, monkeypatch, guard=guard)
    assert out["outcome"] == "escalate"
    assert seen["n"] == 2


def test_replan_is_handled_inside_this_layer(tmp_path, monkeypatch):
    decide = {"action": "replan", "invalidate": [], "reason": "プロセスが違う"}
    mgr = make([PROCESS2, decide, PROCESS2], [
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_NO)]},
        {"done": True, "writes": [("verdict.md", VERDICT_YES)]},   # 実装は carry され QA だけ再実行
    ])
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "done"
    assert out["rounds"] == 2
    assert len(mgr._l3.calls) == 3     # QA は必ず再実行、done の実装は carry される


def test_respec_is_returned_upward(tmp_path, monkeypatch):
    # 仕様が悪いという判断は**この層では直せない**——上の層（L5）へ返す。
    decide = {"action": "respec", "invalidate": [], "reason": "定義が曖昧"}
    mgr = make([PROCESS2, decide], [
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_NO)]},
    ])
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "respec"
    assert "定義が曖昧" in out["reason"]
    assert out["ok"] is False
    assert out["verdict"]["achieved"] == "no"     # 判断材料も一緒に返す


def test_escalate_is_returned_upward(tmp_path, monkeypatch):
    decide = {"action": "escalate", "invalidate": [], "reason": "人手が要る"}
    mgr = make([PROCESS2, decide], [
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_NO)]},
    ])
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "escalate"
    assert "人手が要る" in out["reason"]


def test_budget_exhaustion_becomes_escalate(tmp_path, monkeypatch):
    # 直せるはずでも予算が尽きたら人手へ（自分の封筒は自分で守る）。
    decide = {"action": "rerun", "invalidate": ["result.csv"], "reason": "もう一度"}
    mgr = make([PROCESS2, decide], [
        {"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_NO)]},
    ])
    out = run(mgr, tmp_path, monkeypatch, max_rounds=1)
    assert out["outcome"] == "escalate"
    assert "予算切れ" in out["reason"]
    assert out["rounds"] == 1


def test_failed_task_stops_the_round_and_reports(tmp_path, monkeypatch):
    decide = {"action": "escalate", "invalidate": [], "reason": "実装が失敗した"}
    mgr = make([PROCESS2, decide], [{"done": False}])
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "escalate"
    assert out["verdict"] is None                 # QA まで到達していない
    assert len(mgr._l3.calls) == 1                # 失敗したタスクで止まる


def test_qa_task_is_appended_when_the_process_lacks_it(tmp_path, monkeypatch):
    proc = {"tasks": [{"role": "implementer", "task": "実装", "file": "a.py", "criterion": "動く"}]}
    mgr = make([proc], [{"done": True}, {"done": True, "writes": [("verdict.md", VERDICT_YES)]}])
    out = run(mgr, tmp_path, monkeypatch)
    assert out["tasks"][-1]["role"] == "qa"       # 検証を飛ばして完遂に到達できない（床）
    assert out["outcome"] == "done"


def test_process_artifact_is_written(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch, purpose="不採算商品を特定する")
    text = (tmp_path / "PROCESS.md").read_text(encoding="utf-8")
    assert "implementer" in text and "qa" in text
    assert "不採算商品を特定する" in text          # 目的は上の層から渡ってくる


def test_pjm_prompt_and_contract_come_from_outside_the_code(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch, roles=dict(ROLES, pjm="PJM-ROLE-DOC"))
    system = mgr._l0.calls[0]["messages"][0]["content"]
    assert "PJM-ROLE-DOC" in system                # やり方は役割定義から
    assert "tasks" in system                       # 形はスキーマから

def test_guard_is_checked_between_tasks_not_only_at_round_heads(tmp_path, monkeypatch):
    # 018: 017 再走では1周が締切に収まらず、周の頭の検査は一度も走らなかった。
    # 破壊はタスクの中で起きる——タスク境界で見て、次のタスクを偽の前提の上で走らせない。
    seen = {"n": 0}

    def guard():
        seen["n"] += 1
        return [] if seen["n"] <= 2 else [{"path": "inventory.csv", "status": "modified"}]

    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch, guard=guard)
    assert out["outcome"] == "escalate"
    assert "inventory.csv" in out["reason"]
    assert len(mgr._l3.calls) == 1      # タスク1の後・タスク2の前で止まる


# --- 018-⑥: 締切（deadline）の注入 --------------------------------------------
#
# 層の予算は「周回数」建てで、外部 kill は「分」建て——整合せず、kill は finally を
# 飛ばして観測ゼロを生んだ（017 再走×2）。guard と同型で呼び出し側が締切を注入し、
# 周・タスク境界で見て、時間切れは**部分結果つき escalate** として正常に返す。


def test_deadline_stops_before_any_work(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch, deadline=lambda: True)
    assert out["outcome"] == "escalate"
    assert "時間" in out["reason"]
    assert mgr._l3.calls == []


def test_deadline_between_tasks_returns_partial_results(tmp_path, monkeypatch):
    seen = {"n": 0}

    def deadline():
        seen["n"] += 1
        return seen["n"] > 2      # 周の頭(1)→タスク1前(2)は許し、タスク2前(3)で切れる

    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch, deadline=deadline)
    assert out["outcome"] == "escalate"
    assert "時間" in out["reason"]
    assert len(mgr._l3.calls) == 1
    assert out["tasks"][0].get("done") is True     # 部分結果が返る


def test_deadline_that_never_fires_does_not_interfere(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch, deadline=lambda: False)
    assert out["outcome"] == "done"


# --- 018-④⑤: L3 の Plan をコードが検査する（保護入力・write_scope） -----------
#
# 017 実走: Planner は保護入力を file にする単位や、役割の write_scope の外の成果物
# （read_verification_log.txt）を発明した。規範（プロンプト）は確率的にしか効かない——
# 単位の file は計画の時点でコードが拒否する（L3 の approve スロット）。


def test_plan_lint_rejects_protected_files_and_out_of_scope_files(tmp_path, monkeypatch):
    from mu.l4 import plan_lint
    monkeypatch.chdir(tmp_path)
    task = {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ITEM 行"}
    doc = {"prompt": "QA", "tools": None, "write_scope": "own"}
    approve = plan_lint(task, doc, ["inventory.csv"], lambda e: None)
    units = approve([
        {"task": "mock を作る", "file": "inventory.csv", "criterion": ""},
        {"task": "検証ログ", "file": "read_verification_log.txt", "criterion": ""},
        {"task": "判定書", "file": "verdict.md", "criterion": ""},
    ])
    assert [u["file"] for u in units] == ["verdict.md"]


def test_plan_lint_allows_other_files_for_unrestricted_roles(tmp_path, monkeypatch):
    from mu.l4 import plan_lint
    monkeypatch.chdir(tmp_path)
    task = {"role": "implementer", "task": "実装する", "file": "main.py", "criterion": ""}
    doc = {"prompt": "IMPL", "tools": None, "write_scope": "any"}
    approve = plan_lint(task, doc, ["inventory.csv"], lambda e: None)
    units = approve([
        {"task": "実装", "file": "main.py", "criterion": ""},
        {"task": "補助", "file": "helper.py", "criterion": ""},
        {"task": "入力を作り直す", "file": "inventory.csv", "criterion": ""},
    ])
    assert [u["file"] for u in units] == ["main.py", "helper.py"]   # 保護だけ拒否


def test_plan_lint_that_empties_a_plan_falls_back_to_the_task_itself(tmp_path, monkeypatch):
    # 全滅させると L3 が「empty plan」で失敗しタスクごと死ぬ。タスク自身を1単位として置く。
    from mu.l4 import plan_lint
    monkeypatch.chdir(tmp_path)
    task = {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ITEM 行"}
    doc = {"prompt": "QA", "tools": None, "write_scope": "own"}
    approve = plan_lint(task, doc, [], lambda e: None)
    units = approve([{"task": "別の場所へ", "file": "elsewhere.md", "criterion": ""}])
    assert [u["file"] for u in units] == ["verdict.md"]
    assert units[0]["done"] is False


def test_execute_passes_the_plan_lint_to_l3(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch, protected=["inventory.csv"])
    assert out["outcome"] == "done"
    assert callable(mgr._l3.calls[0]["kwargs"].get("approve"))

# --- 019 Phase4: 契約は確率的な転記に乗せない——system でコードが運ぶ ------------
#
# 019 実走: 判定書契約（＋「FAIL を含む判定書も完成」）は task_goal にだけあり、
# L3 が unit を計画し直すたびに転記から欠落して L2 に届かなかった。
# system は L3→L2 へコードが素通しで運ぶ——契約はそこに載せる（goal にも残す）。


def test_qa_contract_rides_the_system_channel(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch)
    qa_system = mgr._l3.calls[1]["kwargs"].get("system") or ""
    assert "ITEM <番号>" in qa_system                    # 判定書の書式
    assert "不合格は不合格と書いて完成" in qa_system      # 正直な FAIL の承認（019）


def test_the_contract_is_not_injected_into_other_roles(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch)
    impl_system = mgr._l3.calls[0]["kwargs"].get("system") or ""
    assert "ITEM <番号>" not in impl_system

# --- 019 Phase5: 判定書 unit の検査は正準（コード供給）——LLM に発明させない --------
#
# 019p4 実走: L3 が判定書の unit に自作の検査を発明し、その検査自体が壊れて
# （実在しない Write-Content・ParserError・ありえない expect）**正しい判定書を3回**
# 落とした。判定書の中身は read_verdict（コード）が読む——unit の検査は
# 「規定の形式で存在するか」の最小でよい。


def test_plan_lint_replaces_qa_unit_checks_with_the_canonical_check(tmp_path, monkeypatch):
    from mu.l4 import plan_lint
    monkeypatch.chdir(tmp_path)
    task = {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ITEM 行"}
    doc = {"prompt": "QA", "tools": None, "write_scope": "own"}
    approve = plan_lint(task, doc, [], lambda e: None)
    units = approve([{
        "task": "判定書を書く", "file": "verdict.md",
        "check": {"run": "Write-Content nonsense", "expect": "'ITEM 1:' and no code blocks"},
    }])
    assert units[0]["check"]["expect"] == "ITEM 1:"
    assert "verdict.md" in units[0]["check"]["run"]
    assert "Write-Content" not in units[0]["check"]["run"]


def test_plan_lint_fallback_unit_also_gets_the_canonical_check(tmp_path, monkeypatch):
    from mu.l4 import plan_lint
    monkeypatch.chdir(tmp_path)
    task = {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ITEM 行"}
    doc = {"prompt": "QA", "tools": None, "write_scope": "own"}
    approve = plan_lint(task, doc, [], lambda e: None)
    units = approve([{"task": "別の場所へ", "file": "elsewhere.md", "criterion": ""}])
    assert units[0]["file"] == "verdict.md"
    assert units[0]["check"]["expect"] == "ITEM 1:"


def test_plan_lint_leaves_non_qa_checks_alone(tmp_path, monkeypatch):
    # 検査の発明を禁じるのは判定書だけ。実装タスクの check は計画者の裁量のまま。
    from mu.l4 import plan_lint
    monkeypatch.chdir(tmp_path)
    task = {"role": "implementer", "task": "実装する", "file": "main.py", "criterion": ""}
    doc = {"prompt": "IMPL", "tools": None, "write_scope": "any"}
    approve = plan_lint(task, doc, [], lambda e: None)
    units = approve([{
        "task": "実装", "file": "main.py",
        "check": {"run": "python main.py", "expect": "OK"},
    }])
    assert units[0]["check"] == {"run": "python main.py", "expect": "OK"}


# --- 029: 装備（skill）は役割の直後・契約の手前に着せられる ----------------------
#
# skill は層ではなく、役割定義書と同じ場所（層の外のデータ）から同じ経路で着る。
# 違いは濃度（1 task = 0..N）と、**権限を持たない**こと。

SKILLS = {
    "readonly-inputs": {
        "prompt": "SKILL-IMPL-MARKER", "applies_to": ("implementer",),
        "maturity": "confirmed", "description": "x",
    },
    "house-style": {
        "prompt": "SKILL-ALL-MARKER", "applies_to": None,
        "maturity": "confirmed", "description": "x",
    },
    "not-ready": {
        "prompt": "SKILL-DRAFT-MARKER", "applies_to": None,
        "maturity": "draft", "description": "x",
    },
}


def test_skills_are_worn_by_the_task_in_role_skill_contract_order(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch, skills=SKILLS)
    qa_system = mgr._l3.calls[1]["kwargs"]["system"]
    # 職掌 → 装備 → 契約 の順（契約は 019 で確立した「再計画で薄まらない経路」。順序を動かさない）
    assert qa_system.index("QA-MARKER") < qa_system.index("SKILL-ALL-MARKER")
    assert qa_system.index("SKILL-ALL-MARKER") < qa_system.index("ITEM <番号>")


def test_a_skill_reaches_only_the_role_it_names(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch, skills=SKILLS)
    impl_system, qa_system = (mgr._l3.calls[i]["kwargs"]["system"] for i in (0, 1))
    assert "SKILL-IMPL-MARKER" in impl_system
    assert "SKILL-IMPL-MARKER" not in qa_system      # 宛先の無い役割には届かない
    assert "SKILL-ALL-MARKER" in impl_system and "SKILL-ALL-MARKER" in qa_system


def test_draft_skills_never_reach_a_task(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch, skills=SKILLS)
    assert all("SKILL-DRAFT-MARKER" not in c["kwargs"]["system"] for c in mgr._l3.calls)


def test_positions_wear_skills_on_the_lifeline_too(tmp_path, monkeypatch):
    # `applies_to: pjm` を空手形にしない——4ポジションは目的②（プロジェクト方針）が
    # パッケージ自動選択（028）の下でも確実に名指しできる唯一の宛先である。
    skills = {"planning-policy": {"prompt": "SKILL-PJM-MARKER", "applies_to": ("pjm",),
                                  "maturity": "confirmed", "description": "x"}}
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch, skills=skills)
    assert "SKILL-PJM-MARKER" in mgr._l0.calls[0]["messages"][0]["content"]


def test_skills_are_logged_at_the_composition_point(tmp_path, monkeypatch):
    events = []
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch, skills=SKILLS, log=events.append)
    worn = [e for e in events if e[0] == "skills"]
    assert ("skills", "implementer", ["readonly-inputs", "house-style"],
            len("SKILL-IMPL-MARKER\n\nSKILL-ALL-MARKER")) in worn


def test_skills_cannot_widen_the_tools_a_role_receives(tmp_path, monkeypatch):
    # 絶対ルールの行動側の担保: skill を着せても、役割が受け取るツールは変わらない。
    # （宣言側の担保＝権限キーの名指し拒否は test_skill_kb.py）
    roles = dict(ROLES, qa={"prompt": "QA-MARKER", "tools": ["read_file"], "write_scope": "own"})
    bare, equipped = make([PROCESS2], ok2()), make([PROCESS2], ok2())
    run(bare, tmp_path, monkeypatch, roles=roles)
    run(equipped, tmp_path, monkeypatch, roles=roles, skills=SKILLS)
    names = lambda mgr: [f.__name__ for f, _ in mgr._l3.calls[1]["tools"]]
    assert names(equipped) == names(bare)


def test_no_skills_leaves_the_task_system_unchanged(tmp_path, monkeypatch):
    # 029 以前と同一の合成（装備ゼロは no-op）。既存の 300+ テストが測る挙動を動かさない。
    bare, empty = make([PROCESS2], ok2()), make([PROCESS2], ok2())
    run(bare, tmp_path, monkeypatch)
    run(empty, tmp_path, monkeypatch, skills={})
    assert bare._l3.calls[1]["kwargs"]["system"] == empty._l3.calls[1]["kwargs"]["system"]


# --- 030: needs はゲート——満たせなければタスクは実行できない ---------------------
#
# 入力（needs）は宣言される。宣言が満たせないタスクは L3 に渡さず、正直な失敗として
# PjM の decide（rerun / replan）に乗せる。QA の needs はコードが必ず供給する（床）。


def test_a_task_with_unsatisfiable_needs_fails_before_l3_runs(tmp_path, monkeypatch):
    proc = {"tasks": [
        {"role": "implementer", "task": "実装", "file": "result.csv",
         "criterion": "出力", "needs": ["nosuch.csv"]},
    ]}
    decide = {"action": "escalate", "invalidate": [], "reason": "入力が無い"}
    mgr = make([proc, decide], [])
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "escalate"
    assert mgr._l3.calls == []                     # 満たせないタスクは L3 に渡さない
    assert "nosuch.csv" in out["tasks"][0].get("last_failure", "")


def test_a_declared_external_file_that_exists_satisfies_the_gate(tmp_path, monkeypatch):
    (tmp_path / "sales.csv").write_text("data", encoding="utf-8")
    proc = {"tasks": [
        {"role": "implementer", "task": "実装", "file": "result.csv",
         "criterion": "出力", "needs": ["sales.csv"]},
        {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ITEM 行"},
    ]}
    mgr = make([proc], ok2())
    out = run(mgr, tmp_path, monkeypatch)
    assert out["outcome"] == "done"


def test_qa_needs_are_wired_to_the_artifacts(tmp_path, monkeypatch):
    mgr = make([PROCESS2], ok2())
    out = run(mgr, tmp_path, monkeypatch)
    assert out["tasks"][-1]["needs"] == ["result.csv"]


def test_needs_field_is_offered_in_the_pjm_schema(tmp_path, monkeypatch):
    # 形はスキーマが唯一の出所（合意008）。needs もスキーマ経由で PjM に見える。
    mgr = make([PROCESS2], ok2())
    run(mgr, tmp_path, monkeypatch)
    assert "needs" in mgr._l0.calls[0]["messages"][0]["content"]


def test_task_goal_lists_needs_not_all_prior_files(tmp_path, monkeypatch):
    # 参照リストは「先行の done 全部」ではなく宣言した needs（＋SPEC）。
    # 完了タイミングで文脈が変わる非決定性を消す（合意021 の再現性）。
    proc = {"tasks": [
        {"role": "implementer", "task": "設計", "file": "design.md", "criterion": "ある"},
        {"role": "implementer", "task": "下ごしらえ", "file": "helper.py", "criterion": "ある"},
        {"role": "implementer", "task": "実装", "file": "result.csv",
         "criterion": "出力", "needs": ["design.md"]},
        {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ITEM 行"},
    ]}
    mgr = make([proc], [
        {"done": True}, {"done": True}, {"done": True},
        {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
    ])
    run(mgr, tmp_path, monkeypatch)
    goal = mgr._l3.calls[2]["goal"]
    assert "SPEC.md, design.md" in goal
    assert "helper.py" not in goal                 # 宣言していないものは文脈に載せない
