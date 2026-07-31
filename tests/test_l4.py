"""L4（PdM + PjM / Director）のユニットテスト。

specify（PdM）/ process 生成・部分再実行判断（PjM）を L0 のフェイクで、
タスク実行（役割を着た L3）を FakeL3 で差し替え、
「目的→SPEC→プロセス（役割注釈付きタスク列）→逐次実行→verdict 機械読み→
 受理/部分再実行/escalate」の機構を検証する。実サーバは使わない。

核となる受入テスト（合意006）:
- QA は独立タスクとして実行され verdict.md を生む（プロセス末尾に必ず存在＝コード保証）
- 部分再実行: PjM が無効化対象を判断し、コードが依存伝播する。QA は必ず再実行される
- 検証できない/しないまま完了に到達する経路が無い
"""

import json
import types

from mu.l4 import Director


class FakeL0:
    """構造化 chat の代役。dict は JSON で、str はそのまま返す。呼び出しを記録。"""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def chat(self, model, messages, **kwargs):
        self.calls.append({"format": kwargs.get("format"), "messages": messages})
        assert self._responses, "フェイク L0 の応答が尽きた"
        r = self._responses.pop(0)
        content = r if isinstance(r, str) else json.dumps(r)
        return types.SimpleNamespace(message=types.SimpleNamespace(content=content))


class FakeL3:
    """役割を着た1タスク実行（L3）の代役。結果を順に返し、副作用でファイルを書ける。"""

    def __init__(self, results=None):
        self._results = list(results or [])
        self.calls = []

    def run(self, model, goal, tools, **kwargs):
        self.calls.append({"model": model, "goal": goal, "kwargs": kwargs})
        r = self._results.pop(0) if self._results else {"done": True}
        for path, content in r.get("writes", []):
            from pathlib import Path
            Path(path).write_text(content, encoding="utf-8")
        return {"units": [], "done": r.get("done", True), "rounds": 1}


SPEC = {
    "definitions": [{"term": "不採算", "definition": "粗利率が5%未満"}],
    "criteria": [{"text": "result.csv が存在する", "run": "", "expect": ""}],
    "spec": "sales.csv から不採算商品を result.csv に出力する",
}

PROCESS3 = {
    "tasks": [
        {"role": "architect", "task": "設計する", "file": "design.md",
         "criterion": "設計規則を含む"},
        {"role": "implementer", "task": "実装する", "file": "result.csv",
         "criterion": "結果を出力する",
         "check": {"run": "python check.py", "expect": "OK"}},
        {"role": "qa", "task": "検証する", "file": "verdict.md",
         "criterion": "ACHIEVED 行を含む", "model": "qwen-x"},
    ]
}

VERDICT_YES = "ACHIEVED: yes\nREASON: 確認した\nGAP:\n"
VERDICT_NO_IMPL = "ACHIEVED: no\nREASON: 出力が壊れている\nGAP: result.csv の列が欠けている\n"

ROLES = {
    "architect": "ARCH-ROLE-MARKER 構造を定義する",
    "implementer": "IMPL-ROLE-MARKER 実装する",
    "qa": "QA-ROLE-MARKER 判定だけを行う",
}

ok3 = lambda: [
    {"done": True},
    {"done": True},
    {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
]


def make(l0_responses, l3_results=None):
    return Director(FakeL0(l0_responses), l3=FakeL3(l3_results))


def run(agent, tmp_path, monkeypatch, **kw):
    monkeypatch.chdir(tmp_path)
    kw.setdefault("roles", ROLES)
    kw.setdefault("models", ["m", "qwen-x"])
    return agent.run("m", "この売上表から不採算商品を特定してくれ", [], **kw)


def test_happy_path_process_runs_and_verdict_accepts(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert result["escalated"] is False
    assert len(agent._l3.calls) == 3
    assert result["assessment"]["achieved"] == "yes"
    assert all(t["done"] for t in result["tasks"])


def test_process_artifact_is_written(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch)
    text = (tmp_path / "PROCESS.md").read_text(encoding="utf-8")
    assert "architect" in text and "qa" in text
    assert "design.md" in text and "verdict.md" in text


def test_role_doc_is_prepended_to_task_system(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, system="ENV-XYZ")
    systems = [c["kwargs"].get("system") or "" for c in agent._l3.calls]
    assert "ARCH-ROLE-MARKER" in systems[0]
    assert "IMPL-ROLE-MARKER" in systems[1]
    assert "QA-ROLE-MARKER" in systems[2]
    assert all("ENV-XYZ" in s for s in systems)  # env preamble も全タスクに届く


def test_pjm_model_assignment_is_honored_within_pool(tmp_path, monkeypatch):
    # 人選: PjM がタスクに指定したモデルは、許可プール内なら使われる。
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, models=["m", "qwen-x"])
    assert agent._l3.calls[2]["model"] == "qwen-x"  # QA タスクは別ファミリー
    assert agent._l3.calls[0]["model"] == "m"


def test_model_outside_pool_falls_back_to_default(tmp_path, monkeypatch):
    proc = {"tasks": [dict(PROCESS3["tasks"][2], model="unknown-model")]}
    agent = make([SPEC, proc], [{"done": True, "writes": [("verdict.md", VERDICT_YES)]}])
    run(agent, tmp_path, monkeypatch, models=["m"])
    assert agent._l3.calls[0]["model"] == "m"


def test_task_goal_contains_file_criterion_check(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch)
    goal = agent._l3.calls[1]["goal"]
    assert "result.csv" in goal
    assert "python check.py" in goal and "OK" in goal


def test_qa_task_is_appended_when_process_lacks_it(tmp_path, monkeypatch):
    # コード保証: プロセス末尾に QA タスクが無ければ足す（検証を飛ばして完遂に到達できない）。
    proc = {"tasks": [{"role": "implementer", "task": "実装", "file": "a.py", "criterion": "動く"}]}
    agent = make([SPEC, proc], [
        {"done": True},
        {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
    ])
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert result["tasks"][-1]["role"] == "qa"
    assert len(agent._l3.calls) == 2


def test_verdict_no_triggers_pjm_partial_rerun(tmp_path, monkeypatch):
    # 部分再実行: verdict no → PjM が実装タスクだけ無効化 → 実装と QA だけ再実行。
    decide = {"action": "rerun", "invalidate": ["result.csv"], "reason": "実装の出力不良"}
    agent = make(
        [SPEC, PROCESS3, decide],
        [
            {"done": True},                                            # architect
            {"done": True},                                            # implementer
            {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]},  # qa → no
            {"done": True},                                            # implementer 再実行
            {"done": True, "writes": [("verdict.md", VERDICT_YES)]},   # qa 再実行 → yes
        ],
    )
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert len(agent._l3.calls) == 5  # architect は再実行されない
    assert result["rounds"] == 2


def test_invalidation_propagates_along_file_dependencies(tmp_path, monkeypatch):
    # design.md を無効化すると、design.md に依存する実装タスクも連鎖的に無効化される。
    proc = {"tasks": [
        {"role": "architect", "task": "設計する", "file": "design.md", "criterion": "規則"},
        {"role": "implementer", "task": "design.md に従い実装する", "file": "app.py",
         "criterion": "design.md の規則に適合"},
        {"role": "qa", "task": "検証", "file": "verdict.md", "criterion": "ACHIEVED"},
    ]}
    decide = {"action": "rerun", "invalidate": ["design.md"], "reason": "設計不備"}
    agent = make(
        [SPEC, proc, decide],
        [
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]},
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
        ],
    )
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert len(agent._l3.calls) == 6  # 3タスク全部が再実行された（設計→実装→QA）


def test_qa_is_always_invalidated_on_rerun(tmp_path, monkeypatch):
    # PjM が QA を無効化リストに入れ忘れても、コードが必ず QA を再実行させる。
    decide = {"action": "rerun", "invalidate": ["result.csv"], "reason": "x"}
    agent = make(
        [SPEC, PROCESS3, decide],
        [
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]},
            {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
        ],
    )
    result = run(agent, tmp_path, monkeypatch)
    qa_runs = [c for c in agent._l3.calls if "verdict.md" in c["goal"]]
    assert len(qa_runs) == 2  # QA は必ず再実行


def test_missing_or_unparseable_verdict_is_uncertain_and_escalates(tmp_path, monkeypatch):
    # QA が verdict を書けなかった/壊れていたら uncertain（安全側）→ 上がる。
    agent = make(
        [SPEC, PROCESS3, {"action": "escalate", "invalidate": [], "reason": "判定不能"}],
        [{"done": True}, {"done": True},
         {"done": True, "writes": [("verdict.md", "こわれた判定")]}],
    )
    result = run(agent, tmp_path, monkeypatch, max_rounds=1)
    assert result["achieved"] is False
    assert result["escalated"] is True
    assert result["assessment"]["achieved"] == "uncertain"


def test_broken_pjm_decision_escalates_safely(tmp_path, monkeypatch):
    agent = make(
        [SPEC, PROCESS3, "not json"],
        [{"done": True}, {"done": True},
         {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]}],
    )
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is False
    assert result["escalated"] is True


def test_respec_action_revises_spec_and_rebuilds_process(tmp_path, monkeypatch):
    decide = {"action": "respec", "invalidate": [], "reason": "定義が誤り"}
    spec2 = dict(SPEC, spec="改訂版仕様")
    agent = make(
        [SPEC, PROCESS3, decide, spec2, PROCESS3],
        [
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]},
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
        ],
    )
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert result["spec"]["spec"] == "改訂版仕様"
    assert len(agent._l3.calls) == 6  # respec 後は全タスクやり直し


def test_replan_carries_done_but_never_qa(tmp_path, monkeypatch):
    decide = {"action": "replan", "invalidate": [], "reason": "プロセス構成を変える"}
    agent = make(
        [SPEC, PROCESS3, decide, PROCESS3],
        [
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]},
            # replan 後: design.md / result.csv は done を引き継ぎ、QA だけ再実行
            {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
        ],
    )
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert len(agent._l3.calls) == 4


def test_failed_task_stops_round_and_goes_to_pjm(tmp_path, monkeypatch):
    # タスク失敗（L3 done=False）は即 PjM 判断へ。後続タスクは実行しない。
    decide = {"action": "escalate", "invalidate": [], "reason": "無理"}
    agent = make([SPEC, PROCESS3, decide], [{"done": False}])
    result = run(agent, tmp_path, monkeypatch, max_rounds=1)
    assert result["escalated"] is True
    assert len(agent._l3.calls) == 1  # architect で止まり implementer/qa は走らない


def test_deterministic_criteria_check_failure_blocks_acceptance(tmp_path, monkeypatch):
    # 決定論の床: spec の criteria check がコードで落ちれば verdict yes でも受理しない。
    from mu.l1 import ToolResult
    spec = dict(SPEC, criteria=[{"text": "検査", "run": "python v.py", "expect": "V-OK"}])
    calls = []

    def execute_command(command: str) -> ToolResult:
        """実行する。"""
        calls.append(command)
        return ToolResult("exit=1\nNG", ok=False)

    decide = {"action": "escalate", "invalidate": [], "reason": "check が落ちる"}
    agent = make([spec, PROCESS3, decide], ok3())
    monkeypatch.chdir(tmp_path)
    result = agent.run("m", "purpose", [(execute_command, "execute_command(command)")],
                       roles=ROLES, models=["m", "qwen-x"], max_rounds=1)
    assert result["achieved"] is False
    assert result["escalated"] is True


def test_review_feedback_triggers_respec_cycle(tmp_path, monkeypatch):
    decisions = [{"accept": False, "feedback": "閾値は3%にして"}, {"accept": True}]
    spec2 = dict(SPEC, spec="3%版")
    agent = make(
        [SPEC, PROCESS3, spec2, PROCESS3],
        [
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
            {"done": True}, {"done": True},
            {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
        ],
    )
    result = run(agent, tmp_path, monkeypatch, review=lambda r: decisions.pop(0))
    assert result["achieved"] is True
    assert result["escalated"] is False
    assert result["spec"]["spec"] == "3%版"


def test_load_roles_reads_directory(tmp_path):
    from mu.l4 import load_roles
    d = tmp_path / "roles"
    d.mkdir()
    (d / "qa.md").write_text("QA-DOC", encoding="utf-8")
    (d / "architect.md").write_text("ARCH-DOC", encoding="utf-8")
    roles = load_roles(str(d))
    assert roles == {"architect": "ARCH-DOC", "qa": "QA-DOC"}


def test_specify_and_process_prompts_carry_env(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, system="ENV-PS-MARKER")
    specify_system = agent._l0.calls[0]["messages"][0]["content"]
    process_system = agent._l0.calls[1]["messages"][0]["content"]
    assert "ENV-PS-MARKER" in specify_system
    assert "ENV-PS-MARKER" in process_system


def test_process_prompt_lists_roles_and_models(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, models=["m", "qwen-x"])
    process_user = agent._l0.calls[1]["messages"][1]["content"]
    assert "architect" in process_user and "qa" in process_user
    assert "qwen-x" in process_user
