"""L5（目的の層 / PdM）のユニットテスト——L4 を通した全体の機構もここで検証する。

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

from mu.l4 import Manager
from mu.l5 import Director


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
        self.calls.append({"model": model, "goal": goal, "tools": tools, "kwargs": kwargs})
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

# 017: 判定書は受入基準ごとの二値。総合判定は書かせず、集約はコードが行う。
VERDICT_YES = "ITEM 1: PASS — 確認した\nGAP:\n"
VERDICT_NO_IMPL = "ITEM 1: FAIL — 出力が壊れている\nGAP: result.csv の列が欠けている\n"

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
    l0 = FakeL0(l0_responses)                    # 2層が同じ L0 を順に使う（実機と同じ並び）
    return Director(l0, l4=Manager(l0, l3=FakeL3(l3_results)))


def run(agent, tmp_path, monkeypatch, **kw):
    monkeypatch.chdir(tmp_path)
    kw.setdefault("roles", ROLES)
    kw.setdefault("models", ["m", "qwen-x"])
    tools = kw.pop("tools", [])
    return agent.run("m", "この売上表から不採算商品を特定してくれ", tools, **kw)


def test_happy_path_process_runs_and_verdict_accepts(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True
    assert result["escalated"] is False
    assert len(agent._l4._l3.calls) == 3
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
    systems = [c["kwargs"].get("system") or "" for c in agent._l4._l3.calls]
    assert "ARCH-ROLE-MARKER" in systems[0]
    assert "IMPL-ROLE-MARKER" in systems[1]
    assert "QA-ROLE-MARKER" in systems[2]
    assert all("ENV-XYZ" in s for s in systems)  # env preamble も全タスクに届く


def test_pjm_model_assignment_is_honored_within_pool(tmp_path, monkeypatch):
    # 人選: PjM がタスクに指定したモデルは、許可プール内なら使われる。
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, models=["m", "qwen-x"])
    assert agent._l4._l3.calls[2]["model"] == "qwen-x"  # QA タスクは別ファミリー
    assert agent._l4._l3.calls[0]["model"] == "m"


def test_model_outside_pool_falls_back_to_default(tmp_path, monkeypatch):
    proc = {"tasks": [dict(PROCESS3["tasks"][2], model="unknown-model")]}
    agent = make([SPEC, proc], [{"done": True, "writes": [("verdict.md", VERDICT_YES)]}])
    run(agent, tmp_path, monkeypatch, models=["m"])
    assert agent._l4._l3.calls[0]["model"] == "m"


def test_task_goal_contains_file_criterion_check(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch)
    goal = agent._l4._l3.calls[1]["goal"]
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
    assert len(agent._l4._l3.calls) == 2


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
    assert len(agent._l4._l3.calls) == 5  # architect は再実行されない
    # 合意009: 予算は各層が自分で持つ。部分再実行は L4 の中で回るので L5 のラウンドは 1。
    assert result["rounds"] == 1
    assert result["l4_rounds"] == 2


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
    assert len(agent._l4._l3.calls) == 6  # 3タスク全部が再実行された（設計→実装→QA）


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
    qa_runs = [c for c in agent._l4._l3.calls if "verdict.md" in c["goal"]]
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
    assert len(agent._l4._l3.calls) == 6  # respec 後は全タスクやり直し


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
    assert len(agent._l4._l3.calls) == 4


def test_failed_task_stops_round_and_goes_to_pjm(tmp_path, monkeypatch):
    # タスク失敗（L3 done=False）は即 PjM 判断へ。後続タスクは実行しない。
    decide = {"action": "escalate", "invalidate": [], "reason": "無理"}
    agent = make([SPEC, PROCESS3, decide], [{"done": False}])
    result = run(agent, tmp_path, monkeypatch, max_rounds=1)
    assert result["escalated"] is True
    assert len(agent._l4._l3.calls) == 1  # architect で止まり implementer/qa は走らない


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
    from mu.role_kb import load_roles
    d = tmp_path / "roles"
    d.mkdir()
    (d / "qa.md").write_text("QA-DOC", encoding="utf-8")
    (d / "architect.md").write_text("ARCH-DOC", encoding="utf-8")
    # 合意007 B1 で返り値が {role名: 本文} → {role名: {prompt, tools, write_scope}} に変わった
    # （権限も役割定義に属するデータだから）。frontmatter が無い定義書は無制限として読む。
    roles = load_roles(str(d))
    assert roles == {
        "architect": {"prompt": "ARCH-DOC", "tools": None, "write_scope": "any"},
        "qa": {"prompt": "QA-DOC", "tools": None, "write_scope": "any"},
    }


def test_load_roles_composes_multiple_sets(tmp_path):
    # 025 B: ロールセットの合成。「どのセットをロードするか」がユーザーの意思表示になる。
    from mu.role_kb import load_roles
    core = tmp_path / "core"
    novel = tmp_path / "novel"
    core.mkdir(), novel.mkdir()
    (core / "qa.md").write_text("QA-DOC", encoding="utf-8")
    (novel / "writer.md").write_text("WRITER-DOC", encoding="utf-8")
    roles = load_roles(str(core), str(novel))
    assert set(roles) == {"qa", "writer"}
    assert roles["writer"]["prompt"] == "WRITER-DOC"


def test_load_roles_collision_names_both_sources(tmp_path):
    # 025 B の床: 同名役割の静かな上書きは、今回取り除きたい不透明さそのもの。
    # どちらが勝ったかを推測させず、役割名と両方の出所を名指しして落とす。
    import pytest
    from mu.role_kb import load_roles
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir(), b.mkdir()
    (a / "qa.md").write_text("QA-A", encoding="utf-8")
    (b / "qa.md").write_text("QA-B", encoding="utf-8")
    with pytest.raises(ValueError) as e:
        load_roles(str(a), str(b))
    msg = str(e.value)
    assert "qa" in msg and str(a) in msg and str(b) in msg


def test_missing_positions_reports_undefined_core_names(tmp_path):
    # 025 B の床: コードが名前を知る4ポジション（合意024）の不足を可視化する。
    # エラーにはしない——「定義書が無ければ知識ゼロで動いて失敗する」哲学のまま。
    from pathlib import Path as _P
    from mu.role_kb import load_roles, missing_positions
    d = tmp_path / "roles"
    d.mkdir()
    (d / "qa.md").write_text("QA-DOC", encoding="utf-8")
    (d / "writer.md").write_text("WRITER-DOC", encoding="utf-8")   # ポジション外は無関係
    assert missing_positions(load_roles(str(d))) == ("pdm", "pjm", "implementer")
    repo_roles = load_roles(str(_P(__file__).resolve().parent.parent / "roles"))
    assert missing_positions(repo_roles) == ()


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


def test_process_prompt_staffing_list_excludes_l4_positions(tmp_path, monkeypatch):
    # 025 継ぎ目修理: pjm.md は「listed role names だけを使え」と言う——一覧（見せる範囲）は
    # 人選の検証（task_roles＝有効な範囲）と一致していなければならない。pdm/pjm を載せると
    # 人選しても implementer へ静かにフォールバックするだけの罠になる。
    roles = dict(ROLES, pdm="PDM-POSITION-MARKER 目的を仕様に", pjm="PJM-POSITION-MARKER 進行を管理")
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=roles)
    process_user = agent._l0.calls[1]["messages"][1]["content"]
    assert "architect" in process_user and "qa" in process_user   # 人選対象は載る
    assert "PDM-POSITION-MARKER" not in process_user              # ポジションは載せない
    assert "PJM-POSITION-MARKER" not in process_user


# --- C1（合意007）: 検出した矛盾を独断解決させない -----------------------------
#
# 難課題 H3 の観測: PdM は矛盾（完全除去 かつ 1文字も変えるな）を検出しながら
# 人間に上げず、退化解（0バイトファイル）を仕様として採用し全層が忠実に「達成」した。
# 対処は三重 — (a) specify の規範 / (d) feasible 申告＋コード分岐 / (b) QA が目的原文と照合。

INFEASIBLE_SPEC = {
    "feasible": False,
    "conflicts": ["『個人情報を完全に除去』と『1文字も変えるな』は同時に満たせない"],
    "definitions": [],
    "criteria": [],
    "spec": "",
}


def test_infeasible_purpose_escalates_without_starting_the_process(tmp_path, monkeypatch):
    # (d) 決定論の分岐: feasible=false なら PjM を起動せず即 escalate（握り潰し経路を塞ぐ）。
    agent = make([INFEASIBLE_SPEC], [])
    monkeypatch.chdir(tmp_path)
    result = agent.run("m", "個人情報を完全に除去せよ。ただし1文字も変えるな", [], roles=ROLES)
    assert result["achieved"] is False
    assert result["escalated"] is True
    assert len(agent._l0.calls) == 1     # PjM（プロセス生成）は呼ばれない
    assert agent._l4._l3.calls == []         # タスクは1つも実行されない
    assert result["tasks"] == []
    assert "1文字も変えるな" in result["assessment"]["gap"]
    text = (tmp_path / "SPEC.md").read_text(encoding="utf-8")
    assert "充足不能" in text and "1文字も変えるな" in text   # 人間が読める形で残る


def test_missing_feasible_field_is_treated_as_feasible(tmp_path, monkeypatch):
    # 申告できないモデルで常に止まると自律の到達距離が測れない（合意007 決定4）。
    # 明示的な false だけを分岐条件にする。
    agent = make([SPEC, PROCESS3], ok3())
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True


def test_respec_declaring_infeasible_escalates_immediately(tmp_path, monkeypatch):
    # respec 経由で矛盾が判明した場合も、プロセスを組み直さずその場で人間へ上げる。
    decide = {"action": "respec", "invalidate": [], "reason": "定義が矛盾している"}
    agent = make(
        [SPEC, PROCESS3, decide, INFEASIBLE_SPEC],
        [{"done": True}, {"done": True},
         {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]}],
    )
    result = run(agent, tmp_path, monkeypatch, max_rounds=3)
    assert result["escalated"] is True
    assert len(agent._l4._l3.calls) == 3     # 2周目のタスクは走らない


def test_qa_task_goal_carries_the_original_purpose(tmp_path, monkeypatch):
    # (b) QA の二重化: SPEC が目的の制約を弱めていないか検査できるよう、目的の原文を接地する。
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch)
    goals = [c["goal"] for c in agent._l4._l3.calls]
    assert "不採算商品を特定" in goals[2]
    assert "弱め" in goals[2]
    assert "不採算商品を特定" not in goals[0]   # 他役割は従来どおり SPEC 経由


def test_specify_prompt_forbids_weakening_constraints(tmp_path, monkeypatch):
    # (a) 規範: 制約を弱めた仕様を作るな。
    # 合意008 以降、規範は**やり方**なので KB（roles/pdm.md）にあり、コードは形だけを供給する。
    from pathlib import Path as _P
    from mu.role_kb import load_roles
    roles = load_roles(str(_P(__file__).resolve().parent.parent / "roles"))
    assert "weaken" in roles["pdm"]["prompt"].lower()        # 規範は KB にある

    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=roles)
    specify_system = agent._l0.calls[0]["messages"][0]["content"]
    assert "weaken" in specify_system.lower()                # そのまま system に届く
    assert "feasible" in specify_system                      # 形はスキーマ由来で供給される


# --- C2（合意007）: PdM を入力の実物に接地する ---------------------------------
#
# sales×12b の観測: 仕様が sales.csv のヘッダーを2度発明し、実物との不一致が
# respec と入力破壊の起点になった。仕様を作る前に実物を見せる（呼び出し側が事実を前置する形）。

def test_specify_sees_the_real_input_files(tmp_path, monkeypatch):
    (tmp_path / "sales.csv").write_text("商品ID,数量,単価\np008,3,120\n", encoding="utf-8")
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch)
    specify_user = agent._l0.calls[0]["messages"][1]["content"]
    assert "sales.csv" in specify_user
    assert "商品ID,数量,単価" in specify_user      # ヘッダーの実物が渡る（発明させない）


def test_grounding_excludes_generated_artifacts(tmp_path, monkeypatch):
    # 前走の SPEC.md / PROCESS.md は入力ではない（自分の生成物を入力と誤認させない）。
    (tmp_path / "SPEC.md").write_text("OLD-SPEC-MARKER", encoding="utf-8")
    (tmp_path / "PROCESS.md").write_text("OLD-PROCESS-MARKER", encoding="utf-8")
    (tmp_path / "input.txt").write_text("REAL-INPUT", encoding="utf-8")
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch)
    specify_user = agent._l0.calls[0]["messages"][1]["content"]
    assert "REAL-INPUT" in specify_user
    assert "OLD-SPEC-MARKER" not in specify_user
    assert "OLD-PROCESS-MARKER" not in specify_user


def test_respecify_also_sees_the_real_input_files(tmp_path, monkeypatch):
    # respec は入力破壊の起点だった経路。改訂時にも実物を見せる。
    (tmp_path / "sales.csv").write_text("商品ID,数量,単価\np008,3,120\n", encoding="utf-8")
    decide = {"action": "respec", "invalidate": [], "reason": "ヘッダーが違う"}
    agent = make(
        [SPEC, PROCESS3, decide, SPEC, PROCESS3],
        [{"done": True}, {"done": True},
         {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]}] + ok3(),
    )
    run(agent, tmp_path, monkeypatch, max_rounds=2)
    respecify_user = agent._l0.calls[3]["messages"][1]["content"]
    assert "商品ID,数量,単価" in respecify_user


def test_grounding_truncates_large_files(tmp_path):
    from mu.l5 import _input_grounding
    (tmp_path / "big.txt").write_text("x" * 50_000, encoding="utf-8")
    text = _input_grounding(str(tmp_path), set())
    assert "big.txt" in text
    assert len(text) < 2_000            # 先頭だけ。文脈を食い潰さない
    assert "50000 bytes" in text        # 実サイズは見える


def test_grounding_is_empty_when_no_inputs(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch)
    specify_user = agent._l0.calls[0]["messages"][1]["content"]
    assert specify_user.startswith("PURPOSE:")
    assert "EXISTING" not in specify_user


# --- B1（合意007）: 役割の職掌を権限で守る -------------------------------------
#
# f1×12b r2 の観測: QA が成果物を自分で修正してから合格判定した（自己修正→自己承認）。
# role プロンプトの「実装しない」は確率的にしか効かない。権限はデータ（roles/*.md）に置き、
# コードが適用する。PjM が出せるのは role 名だけなので、権限は PjM から書き換えられない。

from mu.l1 import ToolResult


def perm_tools():
    """権限テスト用のツール群。呼ばれた実引数を記録する。"""
    seen = []

    def write_file(path: str, content: str) -> ToolResult:
        """書く。"""
        seen.append(("write_file", path))
        return ToolResult("wrote", ok=True, facts={"path": path})

    def edit_file(path: str, old: str, new: str) -> ToolResult:
        """直す。"""
        seen.append(("edit_file", path))
        return ToolResult("edited", ok=True, facts={"path": path})

    def read_file(path: str) -> ToolResult:
        """読む。"""
        seen.append(("read_file", path))
        return ToolResult("content", ok=True, facts={"path": path})

    return [(write_file, "write_file(path, content)"), (edit_file, "edit_file(path, old, new)"),
            (read_file, "read_file(path)")], seen


PERM_ROLES = {
    "architect": {"prompt": "ARCH-ROLE-MARKER", "tools": None, "write_scope": "any"},
    "implementer": {"prompt": "IMPL-ROLE-MARKER", "tools": None, "write_scope": "any"},
    "qa": {"prompt": "QA-ROLE-MARKER", "tools": ["read_file", "write_file"], "write_scope": "own"},
}


def tools_of(agent, i):
    return {f.__name__: f for f, _ in agent._l4._l3.calls[i]["tools"]}


def test_qa_cannot_write_files_other_than_its_own_output(tmp_path, monkeypatch):
    tools, seen = perm_tools()
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=PERM_ROLES, tools=tools)
    qa_write = tools_of(agent, 2)["write_file"]

    denied = qa_write("result.csv", "勝手に直した成果物")
    assert denied.ok is False
    assert denied.facts.get("denied") is True
    assert ("write_file", "result.csv") not in seen      # 実ツールに到達していない

    allowed = qa_write("verdict.md", "ACHIEVED: no\n")
    assert allowed.ok is True
    assert ("write_file", "verdict.md") in seen          # 自分の出力ファイルは書ける


def test_qa_does_not_receive_tools_outside_its_allowlist(tmp_path, monkeypatch):
    tools, _ = perm_tools()
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=PERM_ROLES, tools=tools)
    assert "edit_file" not in tools_of(agent, 2)          # QA には渡さない
    assert "read_file" in tools_of(agent, 2)


def test_other_roles_keep_full_tools(tmp_path, monkeypatch):
    # 塞ぐのは役割の職掌違反であって能力ではない（合意007 決定4）。実装者は制限しない。
    tools, seen = perm_tools()
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=PERM_ROLES, tools=tools)
    impl = tools_of(agent, 1)
    assert set(impl) == {"write_file", "edit_file", "read_file"}
    assert impl["write_file"]("scratch.txt", "中間ファイル").ok is True
    assert ("write_file", "scratch.txt") in seen


def test_plain_string_roles_still_work(tmp_path, monkeypatch):
    # 旧形式（role名→本文の dict）を渡す呼び出し側を壊さない。
    tools, seen = perm_tools()
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=ROLES, tools=tools)
    assert "QA-ROLE-MARKER" in (agent._l4._l3.calls[2]["kwargs"].get("system") or "")
    assert tools_of(agent, 2)["write_file"]("anything.txt", "x").ok is True


def test_denied_write_is_logged(tmp_path, monkeypatch):
    events = []
    tools, _ = perm_tools()
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=PERM_ROLES, tools=tools, log=events.append)
    tools_of(agent, 2)["write_file"]("result.csv", "x")
    kinds = [e[0] for e in events if isinstance(e, tuple)]
    assert "permission_denied" in kinds      # 塞いだことは見える（観測を殺さない）
    assert "tool_withheld" in kinds


def test_load_roles_parses_permission_frontmatter(tmp_path):
    from mu.role_kb import load_roles
    d = tmp_path / "roles"
    d.mkdir()
    (d / "qa.md").write_text(
        "---\ntools: read_file, execute_command\nwrite_scope: own\n---\n# role: qa\nQA-DOC\n",
        encoding="utf-8",
    )
    (d / "architect.md").write_text("ARCH-DOC", encoding="utf-8")   # frontmatter 無しも受ける
    roles = load_roles(str(d))
    assert roles["qa"]["tools"] == ["read_file", "execute_command"]
    assert roles["qa"]["write_scope"] == "own"
    assert "QA-DOC" in roles["qa"]["prompt"]
    assert "tools:" not in roles["qa"]["prompt"]        # frontmatter は本文に混ぜない
    assert roles["architect"] == {"prompt": "ARCH-DOC", "tools": None, "write_scope": "any"}


def test_repo_role_kb_declares_the_qa_guard():
    # 実際のナレッジベース（roles/）が QA の権限を宣言していること。
    from pathlib import Path as _P
    from mu.role_kb import load_roles
    roles = load_roles(str(_P(__file__).resolve().parent.parent / "roles"))
    assert roles["qa"]["write_scope"] == "own"
    assert "edit_file" not in (roles["qa"]["tools"] or [])
    assert roles["implementer"]["write_scope"] == "any"


# --- 008: 役割定義は外、コアは「位置と契約と床」だけ ---------------------------
#
# 師匠のイメージ:「L4 のコードは役割定義を読んで着せ、決定論の床を回すだけ」。
# 切り分けは「位置は不変・中身は変動」——そこに PdM が居ることは不変、どういう PdM かは変動。
# ミニマムは「役割を認識しているが知識が無い状態」。

PDM_DOC = """あなたは PdM である。PDM-PREAMBLE-MARKER

## specify
SPECIFY-BODY-MARKER 目的を仕様にせよ。

## respecify
RESPECIFY-BODY-MARKER 仕様を改訂せよ。
"""

PJM_DOC = """あなたは PjM である。PJM-PREAMBLE-MARKER

## process
PROCESS-BODY-MARKER プロセスを編め。

## decide
DECIDE-BODY-MARKER 次の一手を決めよ。
"""

ROLES5 = dict(ROLES, pdm=PDM_DOC, pjm=PJM_DOC)


def test_pdm_prompt_comes_from_the_role_doc(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=ROLES5)
    specify_system = agent._l0.calls[0]["messages"][0]["content"]
    assert "PDM-PREAMBLE-MARKER" in specify_system      # 役割共通の前文
    assert "SPECIFY-BODY-MARKER" in specify_system      # その仕事の節
    assert "RESPECIFY-BODY-MARKER" not in specify_system  # 別の節は混ざらない


def test_pjm_prompts_come_from_the_role_doc(tmp_path, monkeypatch):
    decide = {"action": "escalate", "invalidate": [], "reason": "打ち切り"}
    agent = make([SPEC, PROCESS3, decide], [
        {"done": True}, {"done": True},
        {"done": True, "writes": [("verdict.md", VERDICT_NO_IMPL)]},
    ])
    run(agent, tmp_path, monkeypatch, roles=ROLES5, max_rounds=1)
    process_system = agent._l0.calls[1]["messages"][0]["content"]
    decide_system = agent._l0.calls[2]["messages"][0]["content"]
    assert "PROCESS-BODY-MARKER" in process_system
    assert "DECIDE-BODY-MARKER" in decide_system
    assert "PJM-PREAMBLE-MARKER" in process_system and "PJM-PREAMBLE-MARKER" in decide_system


def test_missing_role_doc_runs_without_instruction_and_logs_it(tmp_path, monkeypatch):
    # ミニマム＝「役割を認識しているが知識が無い状態」。既定プロンプトへフォールバックしない。
    events = []
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles={}, log=events.append)
    specify_system = agent._l0.calls[0]["messages"][0]["content"]
    assert "PURPOSE" not in specify_system           # やり方の指示は無い
    assert len(specify_system) < 400                 # 契約（返す形）だけが残る
    kinds = [e[0] for e in events if isinstance(e, tuple)]
    assert "role_doc_missing" in kinds               # 静かに劣化させない


def test_output_shape_comes_from_the_schema_not_the_role_doc(tmp_path, monkeypatch):
    # 契約はポジション側（コア）の持ち物。定義書に JSON の形を書かせない。
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=ROLES5)
    specify_system = agent._l0.calls[0]["messages"][0]["content"]
    for key in ("feasible", "conflicts", "definitions", "criteria", "spec"):
        assert key in specify_system                 # スキーマ由来の1行が供給される
    process_system = agent._l0.calls[1]["messages"][0]["content"]
    assert "tasks" in process_system


def test_role_docs_do_not_declare_the_json_shape():
    # 実 KB の規律: 形はスキーマが唯一の出所。定義書が二重に宣言しない。
    from pathlib import Path as _P
    from mu.role_kb import load_roles
    roles = load_roles(str(_P(__file__).resolve().parent.parent / "roles"))
    assert {"pdm", "pjm", "architect", "implementer", "qa"} <= set(roles)
    for name, doc in roles.items():
        assert "Reply as JSON" not in doc["prompt"], name


def test_core_has_no_lifeline_prompt_constants():
    # コアから生命線プロンプトが消えていること（外に出た＝コード内定数として残っていない）。
    import mu.l4 as l4, mu.l5 as l5
    assert not [n for n in dir(l4) if n.endswith("_SYSTEM")]
    assert not [n for n in dir(l5) if n.endswith("_SYSTEM")]


# --- 008 Phase2: ミニマム定義はコード、拡張・上書きは定義書 ---------------------
#
# 師匠:「ミニマム定義をコード中に残し、定義書で拡張または上書き可能とする」
#      「役割を認識しているが知識が無い状態がミニマム」
# ただし床は上書き不可 — 定義書から検証を消せると、偽・完遂の経路がデータ側から開く。

QA_DOC_OVERRIDE = {
    "prompt": "QA-ROLE-MARKER",
    "tools": None,
    "write_scope": "own",
    "task": "OVERRIDDEN-QA-TASK 受入基準を独立に検証する",
    "file": "judgement.md",
    "criterion": "OVERRIDDEN-CRITERION",
}


def qa_less_process():
    return {"tasks": [{"role": "implementer", "task": "実装", "file": "a.py", "criterion": "動く"}]}


def test_default_qa_task_is_overridable_by_the_role_doc(tmp_path, monkeypatch):
    roles = dict(ROLES, qa=QA_DOC_OVERRIDE)
    agent = make([SPEC, qa_less_process()], [
        {"done": True},
        {"done": True, "writes": [("judgement.md", VERDICT_YES)]},
    ])
    result = run(agent, tmp_path, monkeypatch, roles=roles)
    qa_task = result["tasks"][-1]
    assert qa_task["role"] == "qa"
    assert qa_task["file"] == "judgement.md"                 # 上書きが効く
    assert "OVERRIDDEN-QA-TASK" in qa_task["task"]
    # 上書きは効くが、判定書の契約（床）はコードが必ず足す（008 Phase4 の劣化への対処）
    assert qa_task["criterion"].startswith("OVERRIDDEN-CRITERION")
    assert "ITEM" in qa_task["criterion"]          # 017: 契約は項目ごとの二値
    assert result["achieved"] is True                        # 判定書の場所も追随する


def test_frontmatter_override_keys_survive_the_loader(tmp_path):
    # 023 A1: 上の test_default_qa_task_... は roles dict を手組みで注入しており、
    # 実際の経路（roles/*.md → load_roles）では上書きキーがローダーに捨てられて
    # いた（宣言テスト化）。実経路で「frontmatter に書けば効く」を固定する。
    from mu.role_kb import load_roles
    from mu.process import default_qa_task
    d = tmp_path / "roles"
    d.mkdir()
    (d / "qa.md").write_text(
        "---\ntools: read_file\nwrite_scope: own\n"
        "file: judgement.md\ncriterion: LOADER-CRITERION\n---\nQA-DOC\n",
        encoding="utf-8",
    )
    roles = load_roles(str(d))
    qa = default_qa_task(roles)
    assert qa["file"] == "judgement.md"
    assert qa["criterion"] == "LOADER-CRITERION"
    assert "QA-DOC" in roles["qa"]["prompt"]     # 本文はそのまま


def test_qa_task_presence_is_not_overridable(tmp_path, monkeypatch):
    # 床: 定義書が何を言っても「QA タスクが存在すること」は消せない。
    roles = dict(ROLES, qa={"prompt": "", "tools": None, "write_scope": "own",
                            "task": "", "file": "", "criterion": ""})
    agent = make([SPEC, qa_less_process()], [
        {"done": True},
        {"done": True, "writes": [("verdict.md", VERDICT_YES)]},
    ])
    result = run(agent, tmp_path, monkeypatch, roles=roles)
    assert result["tasks"][-1]["role"] == "qa"
    assert result["tasks"][-1]["file"] == "verdict.md"       # コードのミニマムに落ちる


def test_verdict_format_contract_is_supplied_by_code(tmp_path, monkeypatch):
    # 判定書の書式はコードが正規表現で読む「契約」＝ポジション側の持ち物。
    # 役割定義書が空でも QA には書式が届く。
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles={})
    qa_goal = agent._l4._l3.calls[2]["goal"]
    assert "ITEM <番号>: PASS|FAIL|UNCERTAIN" in qa_goal   # 017: 項目ごとの二値
    assert "総合判定は書かない" in qa_goal and "GAP" in qa_goal
    impl_goal = agent._l4._l3.calls[1]["goal"]
    assert "ACHIEVED:" not in impl_goal                      # 契約は QA のポジションにだけ届く


def test_role_kb_does_not_restate_the_verdict_contract():
    # 実 KB の規律: 契約はコードが唯一の出所。qa.md に書式を二重に書かない。
    from pathlib import Path as _P
    from mu.role_kb import load_roles
    roles = load_roles(str(_P(__file__).resolve().parent.parent / "roles"))
    assert "ACHIEVED: yes | no | uncertain" not in roles["qa"]["prompt"]


def test_artifact_note_is_overridable_by_the_role_doc(tmp_path, monkeypatch):
    pdm = {"prompt": "あなたは PdM である。\n\n## specify\nSPECIFY-BODY\n\n"
                     "## spec-artifact\nSPEC-NOTE-OVERRIDE この仕様書は実験用である。",
           "tools": None, "write_scope": "any"}
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles=dict(ROLES, pdm=pdm))
    text = (tmp_path / "SPEC.md").read_text(encoding="utf-8")
    assert "SPEC-NOTE-OVERRIDE" in text
    assert "## 操作的定義" in text                            # 構造（床）は残る


def test_artifact_note_falls_back_to_the_code_minimum(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    run(agent, tmp_path, monkeypatch, roles={})
    text = (tmp_path / "SPEC.md").read_text(encoding="utf-8")
    assert "直接編集して直してよい" in text                    # コードのミニマム
    assert "## 受入基準" in text


# --- 008 Phase4 の実走で見つかった劣化への対処: 判定書の読み手を頑健にする -------
#
# 契約をコード供給に移した結果、QA が Markdown 見出しで書くようになり、機械読みが空になった。
# 017 で契約は「受入基準ごとの ITEM 行」に変わったが、**装飾を許して判定語は厳格に読む**という
# 作法はそのまま引き継ぐ。総合判定はもう書かせない——集約はコードが行う。

VERDICT_MARKDOWN = """# 検証結果（verdict）

## 受入基準ごとの判定

- **ITEM 1:** PASS — `Get-ChildItem report.txt` により report.txt の存在を確認した

## GAP

なし
"""


def test_verdict_reader_accepts_markdown_decorated_format(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], [
        {"done": True}, {"done": True},
        {"done": True, "writes": [("verdict.md", VERDICT_MARKDOWN)]},
    ])
    result = run(agent, tmp_path, monkeypatch)
    assert result["achieved"] is True                 # 装飾された ITEM 行を読めている
    assert result["assessment"]["items"][0]["verdict"] == "pass"
    assert "report.txt の存在を確認" in result["assessment"]["items"][0]["evidence"]


def test_verdict_without_a_verdict_word_stays_uncertain(tmp_path, monkeypatch):
    # 対照走で実際に起きた形の 017 版: 判定語のない散文。判定語が無ければ合格にしない。
    bad = "全体として要件を満たしていると考えられる。実装は妥当である。\n"
    decide = {"action": "escalate", "invalidate": [], "reason": "判定書が読めない"}
    agent = make([SPEC, PROCESS3, decide], [
        {"done": True}, {"done": True},
        {"done": True, "writes": [("verdict.md", bad)]},
    ])
    result = run(agent, tmp_path, monkeypatch, max_rounds=1)
    assert result["achieved"] is False
    assert result["assessment"]["items"][0]["verdict"] == "uncertain"


def test_a_total_judgement_does_not_override_the_items(tmp_path, monkeypatch):
    # 017: 総合判定は LLM から取り上げた。ACHIEVED 行を書かれても集約はコードが決める。
    text = "ACHIEVED: yes\nREASON: 全部できています\nITEM 1: FAIL — 出力が空だった\n"
    decide = {"action": "escalate", "invalidate": [], "reason": "未達"}
    agent = make([SPEC, PROCESS3, decide], [
        {"done": True}, {"done": True},
        {"done": True, "writes": [("verdict.md", text)]},
    ])
    result = run(agent, tmp_path, monkeypatch, max_rounds=1)
    assert result["achieved"] is False


def test_verdict_reason_is_composed_by_code_not_by_the_llm(tmp_path, monkeypatch):
    # 017: reason は「何項目中いくつ PASS か」をコードが組み立てる（LLM の散文ではない）。
    agent = make([SPEC, PROCESS3], ok3())
    result = run(agent, tmp_path, monkeypatch)
    assert "すべて PASS" in result["assessment"]["reason"]


def test_qa_task_criterion_carries_the_contract(tmp_path, monkeypatch):
    # 契約はコードの持ち物。PjM が書いた QA タスクの成功条件にも足し、
    # L2 Reflect が欠落を落とせるようにする（読み手を頑健にするだけでは書き手が痩せる）。
    agent = make([SPEC, PROCESS3], ok3())
    result = run(agent, tmp_path, monkeypatch)
    qa_task = result["tasks"][-1]
    assert "ITEM" in qa_task["criterion"]
    assert "PASS|FAIL|UNCERTAIN" in qa_task["criterion"]
    assert "ACHIEVED 行を含む" in qa_task["criterion"]      # PjM が書いた分は残る
    assert "ITEM" not in result["tasks"][0]["criterion"]    # 他役割には足さない

# --- 018: 締切と保護一覧の受け渡し（L5 → L4） ----------------------------------


def test_deadline_stops_the_purpose_loop_with_partial_state(tmp_path, monkeypatch):
    # 外部 kill は finally を飛ばし観測ゼロを生む（017 再走×2）。締切は部分結果つきで
    # **正常に返る**こと——タイムアウトを「観測できる失敗」に変える。
    agent = make([SPEC])                      # specify だけ消費。L4 は呼ばれない
    result = run(agent, tmp_path, monkeypatch, deadline=lambda: True)
    assert result["achieved"] is False
    assert result["escalated"] is True
    assert "時間" in result["assessment"]["reason"]
    assert agent._l4._l3.calls == []


def test_deadline_and_protected_are_passed_to_l4(tmp_path, monkeypatch):
    agent = make([SPEC, PROCESS3], ok3())
    result = run(agent, tmp_path, monkeypatch,
                 protected=["inventory.csv"], deadline=lambda: False)
    assert result["achieved"] is True
    assert callable(agent._l4._l3.calls[0]["kwargs"].get("approve"))


# --- 019: 役割定義書の規範（リポジトリの roles/ が宣言していること） -------------


def test_repo_pdm_forbids_assumed_answers_in_expect():
    # 018 実走: PdM が入力の先頭5行から「P003 は死に筋のはず」と推測して expect に焼き込み、
    # 自己矛盾した報告書が機械検査を通過した。答えの仮定はマーカーに置かせない。
    from pathlib import Path as _P
    text = _P("roles/pdm.md").read_text(encoding="utf-8")
    assert "PREDICTED RESULT" in text


def test_repo_qa_declares_honest_fail_as_success():
    from pathlib import Path as _P
    text = _P("roles/qa.md").read_text(encoding="utf-8")
    assert "正直な FAIL" in text


def test_repo_pdm_requires_criteria_to_be_deliverable_properties():
    # 019 実走: 「全商品が計算に含まれていること」（計算の性質）は成果物を読んでも判定できず、
    # QA が商品コード単位の ITEM に流れて read_verdict と噛み合わなかった。
    from pathlib import Path as _P
    text = _P("roles/pdm.md").read_text(encoding="utf-8")
    assert "OF THE DELIVERABLE" in text


def test_repo_pdm_forbids_arithmetic_on_the_excerpt():
    # 019p5 実走: PdM が入力の先頭抜粋の部分和から「P003 純-30」を計算し、SPEC の例示として
    # 焼き込んだ（答え仮定の漏れ先が expect→基準テキスト→仕様本文と移動した3例目）。
    # 根は「抜粋しか見ていないのに算術をする」こと自体——数えるな・足すな。
    from pathlib import Path as _P
    text = _P("roles/pdm.md").read_text(encoding="utf-8")
    assert "arithmetic on an excerpt" in text


# --- 021 修正3件（schedule 実走の偽・不合格への対処） ---------------------------


def test_repo_pdm_forbids_inventing_unseen_invocations():
    # PdM が存在しないサブコマンド `list` を発明（2走とも再現）。見た形だけを使う。
    from pathlib import Path as _P
    text = _P("roles/pdm.md").read_text(encoding="utf-8")
    assert "actually seen" in text


def test_repo_pjm_treats_broken_check_commands_as_spec_defects():
    # PjM は「検査コマンド自体が壊れている」と診断しながら rerun を3回選んだ。
    from pathlib import Path as _P
    text = _P("roles/pjm.md").read_text(encoding="utf-8")
    assert "CHECK COMMAND itself" in text


def test_input_grounding_shows_the_full_docstring_of_scripts(tmp_path):
    # 先頭300字では usage が途中で切れ、PdM が続きを推測する（021 schedule）。
    # スクリプトの自己記述（docstring）は全文見せて、推測の必要を消す。
    from mu.l5 import _input_grounding
    filler = "この行は説明の詰め物である。\n" * 20            # 300字を確実に超える
    (tmp_path / "tool.py").write_text(
        f'"""tool.py — ツールのモック。\n\n{filler}    python tool.py SUBCOMMAND-MARKER\n"""\nprint(1)\n',
        encoding="utf-8",
    )
    text = _input_grounding(str(tmp_path), set())
    assert "SUBCOMMAND-MARKER" in text


def test_input_grounding_shows_ps1_leading_comments(tmp_path):
    from mu.l5 import _input_grounding
    (tmp_path / "run.ps1").write_text(
        "param([string]$Mode = \"quick\")\n# run.ps1 - mock runner\n"
        "# PS1-USAGE-MARKER: use -Mode full for the full run\n$x = 1\n",
        encoding="utf-8",
    )
    text = _input_grounding(str(tmp_path), set())
    assert "PS1-USAGE-MARKER" in text


def test_input_grounding_keeps_plain_files_to_a_short_head(tmp_path):
    from mu.l5 import _input_grounding
    (tmp_path / "data.csv").write_text(
        "".join(f"row{i}\n" for i in range(50)), encoding="utf-8"
    )
    text = _input_grounding(str(tmp_path), set())
    assert "row4" in text
    assert "row9" not in text        # データファイルは従来どおり先頭5行だけ


def test_escalation_reason_reaches_the_result(tmp_path, monkeypatch):
    # 「achieved: false なのに assessment は yes」の走行で、なぜ落ちたかが結果から
    # 読めなかった（021 schedule）。escalate の理由を結果契約に載せる。
    decide = {"action": "escalate", "invalidate": [], "reason": "ESCALATE-REASON-MARKER 人手が要る"}
    agent = make([SPEC, PROCESS3, decide], [
        {"done": True}, {"done": False},     # 実装タスクが失敗 → PjM が escalate
    ])
    result = run(agent, tmp_path, monkeypatch)
    assert result["escalated"] is True
    assert "ESCALATE-REASON-MARKER" in result.get("escalation_reason", "")
