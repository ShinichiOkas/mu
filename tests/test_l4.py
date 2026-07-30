"""L4（目的の層 / Director）のユニットテスト。

specify/assess/respecify（L0 の構造化出力）と D（L3）をフェイクに差し替え、
「目的→定義+完了条件+仕様（artifact）→L3→目的判定→受理/差戻し/上げる」の
機構を検証する。実サーバは使わない。

核となる受入テスト: 判定できないとき黙って 完遂 ✓ を返さず、人間に上がる
（escalated=True）。F1 で観測した偽・完遂（合意005）の再発防止をここに置く。
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
    """D（L3）の代役。goal を記録し、用意した結果を順に返す。"""

    def __init__(self, results=None):
        self.calls = []
        self._results = list(results or [])

    def run(self, model, goal, tools, **kwargs):
        self.calls.append({"goal": goal, "kwargs": kwargs})
        if self._results:
            return self._results.pop(0)
        return {"units": [{"task": "t", "file": "out.txt", "done": True}], "done": True, "rounds": 1}


SPEC = {
    "definitions": [{"term": "不採算", "definition": "粗利率が5%未満"}],
    "criteria": ["result.csv が存在し、不採算商品の行だけを含む"],
    "spec": "sales.csv を読み、粗利率5%未満の商品を result.csv に出力するスクリプトを作る",
}
SPEC2 = dict(SPEC, definitions=[{"term": "不採算", "definition": "粗利率が3%未満"}])
ASSESS_YES = {"achieved": "yes", "reason": "目的の出力が実在する", "gap": ""}
ASSESS_NO = {"achieved": "no", "reason": "欠落あり", "gap": "result.csv に閾値の根拠列が無い"}
ASSESS_UNCERTAIN = {"achieved": "uncertain", "reason": "閾値5%が妥当かは業種知識が要る", "gap": ""}


def make(l0_responses, l3_results=None):
    return Director(FakeL0(l0_responses), l3=FakeL3(l3_results))


def run(agent, tmp_path, monkeypatch, **kw):
    monkeypatch.chdir(tmp_path)
    return agent.run("m", "この売上表から不採算商品を特定してくれ", [], **kw)


def test_happy_path_achieved_without_escalation(tmp_path, monkeypatch):
    agent = make([SPEC, ASSESS_YES])
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert result["escalated"] is False
    assert len(agent._l3.calls) == 1


def test_spec_artifact_is_written_with_purpose_and_definitions(tmp_path, monkeypatch):
    # 定義は artifact（ファイル）: 推測を明示して検証可能な仮定にする（合意005）。
    agent = make([SPEC, ASSESS_YES])
    run(agent, tmp_path, monkeypatch)
    text = (tmp_path / "SPEC.md").read_text(encoding="utf-8")
    assert "この売上表から不採算商品を特定してくれ" in text  # 目的の原文
    assert "不採算" in text and "5%未満" in text            # 操作的定義
    assert "result.csv" in text                             # 完了条件


def test_l3_goal_contains_spec_and_criteria(tmp_path, monkeypatch):
    agent = make([SPEC, ASSESS_YES])
    run(agent, tmp_path, monkeypatch)
    goal = agent._l3.calls[0]["goal"]
    assert SPEC["spec"] in goal
    assert SPEC["criteria"][0] in goal


def test_uncertain_assessment_escalates_instead_of_passing(tmp_path, monkeypatch):
    # 核: 判定できないときは「判定できない」と分かって人間に上げる。黙って完遂✓を返さない。
    agent = make([SPEC, ASSESS_UNCERTAIN])
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is False
    assert result["escalated"] is True
    assert result["assessment"]["achieved"] == "uncertain"


def test_unparseable_assessment_is_uncertain_and_escalates(tmp_path, monkeypatch):
    # 壊れた判定は楽観に倒さない（安全側 = uncertain → 上げる）。
    agent = make([SPEC, "this is not json"])
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is False
    assert result["escalated"] is True


def test_no_with_gap_respecifies_and_retries(tmp_path, monkeypatch):
    # 具体的な欠落（gap）が見えているなら、自律的に仕様を直して再実行する（A）。
    agent = make([SPEC, ASSESS_NO, SPEC2, ASSESS_YES])
    result = run(agent, tmp_path, monkeypatch, max_rounds=3)
    assert result["achieved"] is True
    assert result["rounds"] == 2
    assert len(agent._l3.calls) == 2


def test_respecify_rewrites_spec_artifact(tmp_path, monkeypatch):
    agent = make([SPEC, ASSESS_NO, SPEC2, ASSESS_YES])
    run(agent, tmp_path, monkeypatch, max_rounds=3)
    text = (tmp_path / "SPEC.md").read_text(encoding="utf-8")
    assert "3%未満" in text  # 改訂後の定義に置き換わる


def test_no_at_final_round_escalates(tmp_path, monkeypatch):
    # 上限で gap が残っていれば未達として上げる（自律再試行はしない）。
    agent = make([SPEC, ASSESS_NO])
    result = run(agent, tmp_path, monkeypatch, max_rounds=1)
    assert result["achieved"] is False
    assert result["escalated"] is True


def test_review_slot_feedback_triggers_respecify(tmp_path, monkeypatch):
    # 人間のフィードバックで仕様を直して再実行する（再帰の底 = 人間）。
    decisions = [{"accept": False, "feedback": "閾値は3%にして"}, {"accept": True}]
    seen = []

    def review(report):
        seen.append(report)
        return decisions.pop(0)

    agent = make([SPEC, ASSESS_YES, SPEC2, ASSESS_YES])
    result = run(agent, tmp_path, monkeypatch, review=review, max_rounds=3)
    assert result["achieved"] is True
    assert result["escalated"] is False
    assert len(agent._l3.calls) == 2
    assert seen[0]["assessment"]["achieved"] == "yes"  # review には L4 自身の判定が渡る


def test_review_can_accept_uncertain(tmp_path, monkeypatch):
    # 人間が「これで目的達成」と言えば、L4 が uncertain でも受理される。
    agent = make([SPEC, ASSESS_UNCERTAIN])
    result = run(agent, tmp_path, monkeypatch, review=lambda report: {"accept": True})
    assert result["achieved"] is True
    assert result["escalated"] is False


def test_review_reject_without_feedback_escalates(tmp_path, monkeypatch):
    agent = make([SPEC, ASSESS_YES])
    result = run(agent, tmp_path, monkeypatch, review=lambda report: {"accept": False})
    assert result["achieved"] is False
    assert result["escalated"] is True


def test_assess_evidence_reads_deliverables_from_disk(tmp_path, monkeypatch):
    # 目的判定は plan テキストでなくディスク上の実体に照らす（機序④の L4 版防御）。
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out.txt").write_text("MARKER-CONTENT-XYZ", encoding="utf-8")
    agent = make([SPEC, ASSESS_YES])
    agent.run("m", "purpose", [])
    assess_call = agent._l0.calls[-1]
    user = assess_call["messages"][1]["content"]
    assert "MARKER-CONTENT-XYZ" in user  # ファイルの中身が証拠として渡る
    assert "exists" in user


def test_assess_evidence_marks_missing_files(tmp_path, monkeypatch):
    agent = make([SPEC, ASSESS_YES], l3_results=[
        {"units": [{"task": "t", "file": "ghost.txt", "done": True}], "done": False, "rounds": 1}
    ])
    result = run(agent, tmp_path, monkeypatch)
    user = agent._l0.calls[-1]["messages"][1]["content"]
    assert "MISSING" in user  # done フラグでなくディスクを見て「無い」と言う


def test_unparseable_specify_falls_back_to_purpose(tmp_path, monkeypatch):
    # specify が壊れても落ちず、目的の原文を仕様として L3 に渡す（劣化はログで可視化）。
    events = []
    agent = make(["broken", ASSESS_YES])
    result = run(agent, tmp_path, monkeypatch, log=events.append)
    goal = agent._l3.calls[0]["goal"]
    assert "不採算商品を特定してくれ" in goal
    assert any(e[0] == "spec_fallback" for e in events)


SPEC_CHECKED = {
    "definitions": [{"term": "不採算", "definition": "粗利率が5%未満"}],
    "criteria": [{
        "text": "answer.csv が不採算商品だけを含む",
        "run": "python verify_answer.py",
        "expect": "ANSWER OK",
    }],
    "spec": "sales.csv から不採算商品を answer.csv に出力する",
}


def make_exec(script):
    """execute_command のフェイク（tools 注入用）。"""
    from mu.l1 import ToolResult
    calls = []

    def execute_command(command: str) -> ToolResult:
        """実行する。"""
        calls.append(command)
        return script.get(command, ToolResult("exit=1\n(no entry)", ok=False))

    execute_command.calls = calls
    return (execute_command, "execute_command(command): 実行する。")


def test_criteria_strings_are_normalized_to_objects(tmp_path, monkeypatch):
    # 旧形式（文字列 criteria）も {text, run, expect} に正規化される（後方互換）。
    agent = make([SPEC, ASSESS_YES])
    result = run(agent, tmp_path, monkeypatch)
    c = result["spec"]["criteria"][0]
    assert c["text"] == SPEC["criteria"][0]
    assert c["run"] == "" and c["expect"] == ""


def test_criteria_check_fail_forces_no_without_llm_assess(tmp_path, monkeypatch):
    # criteria の check がコード側で落ちたら、LLM の assess を呼ばず決定的に no。
    monkeypatch.chdir(tmp_path)
    tool = make_exec({})  # どのコマンドも失敗
    agent = make([SPEC_CHECKED])
    result = agent.run("m", "purpose", [tool], max_rounds=1)
    assert result["achieved"] is False
    assert result["escalated"] is True
    assert result["assessment"]["achieved"] == "no"
    assert "ANSWER OK" in result["assessment"]["gap"] or "verify_answer" in result["assessment"]["gap"]
    assert len(agent._l0.calls) == 1  # specify のみ（assess の LLM は呼ばれない）


def test_criteria_check_pass_feeds_assess_evidence(tmp_path, monkeypatch):
    from mu.l1 import ToolResult
    monkeypatch.chdir(tmp_path)
    tool = make_exec({"python verify_answer.py": ToolResult("exit=0\nANSWER OK", ok=True)})
    agent = make([SPEC_CHECKED, ASSESS_YES])
    result = agent.run("m", "purpose", [tool])
    assert result["achieved"] is True
    user = agent._l0.calls[-1]["messages"][1]["content"]
    assert "ANSWER OK" in user  # check の実行結果が証拠として assess に渡る


def test_evidence_includes_workdir_listing_and_criteria_named_files(tmp_path, monkeypatch):
    # 対処2: units のファイル以外でも、criteria が名指しするファイルと workdir 一覧を証拠に含める。
    monkeypatch.chdir(tmp_path)
    (tmp_path / "answer.csv").write_text("MARKER-ANSWER-ROWS", encoding="utf-8")
    (tmp_path / "stray.txt").write_text("x", encoding="utf-8")
    agent = make([SPEC_CHECKED, ASSESS_YES])
    agent.run("m", "purpose", [])
    user = agent._l0.calls[-1]["messages"][1]["content"]
    assert "MARKER-ANSWER-ROWS" in user  # criteria 名指しファイルの中身
    assert "stray.txt" in user           # workdir 一覧


def test_truncated_evidence_downgrades_yes_to_uncertain(tmp_path, monkeypatch):
    # 対処3: 切り詰めた証拠の上で LLM が yes と言っても、コード側で uncertain に落とす。
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out.txt").write_text("A" * 10000, encoding="utf-8")
    agent = make([SPEC, ASSESS_YES])
    result = agent.run("m", "purpose", [])
    assert result["achieved"] is False
    assert result["escalated"] is True
    assert result["assessment"]["achieved"] == "uncertain"
    assert "truncated" in result["assessment"]["reason"]


def test_l3_receives_system_and_limits(tmp_path, monkeypatch):
    agent = make([SPEC, ASSESS_YES])
    run(agent, tmp_path, monkeypatch, system="ENV-XYZ", l3_max=5, l2_max=4, l2_l1_max=3)
    kw = agent._l3.calls[0]["kwargs"]
    assert kw["system"] == "ENV-XYZ"
    assert kw["max_rounds"] == 5
    assert kw["l2_max"] == 4
    assert kw["l2_l1_max"] == 3
