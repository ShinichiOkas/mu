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
    {"role": "qa", "task": "検証する", "file": "verdict.md", "criterion": "ACHIEVED 行"},
]}
VERDICT_YES = "ACHIEVED: yes\nREASON: 確認した\nGAP:\n"
VERDICT_NO = "ACHIEVED: no\nREASON: 列が欠けている\nGAP: 列が足りない\n"
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
