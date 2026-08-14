"""mu/process.py（プロセス＝タスク列の facility）のユニットテスト。

ここで守るのは**コードの決定論**の側だけ——無効化の伝播と、タスク goal の組み立て。
判断（どこを無効化するか）は PjM の仕事であり、このモジュールの責務ではない。

030: 入力は needs で明示宣言される。無効化の伝播は宣言された needs 辺だけを走り、
言及ベースの推定は計画時 lint に降格した（依存グラフの真実の出所は needs の1つ）。
"""

from mu.process import invalidate, needs_hint, task_goal, unmet_needs


def _task(file, *, role="implementer", task="", criterion="", check=None, done=True,
          needs=None):
    t = {"role": role, "task": task or f"{file} を作る", "file": file,
         "criterion": criterion or f"{file} が正しいこと", "done": done,
         "needs": list(needs or [])}
    if check:
        t["check"] = check
    return t


# --- 無効化の伝播（030: 宣言された needs 辺だけを走る） -------------------------

def test_named_file_is_invalidated():
    tasks = [_task("a.md"), _task("b.md")]
    invalidate(tasks, ["a.md"])
    assert tasks[0]["done"] is False
    assert tasks[1]["done"] is True


def test_later_task_that_declares_the_file_as_a_need_is_invalidated():
    tasks = [_task("data.csv"), _task("report.md", needs=["data.csv"])]
    invalidate(tasks, ["data.csv"])
    assert [t["done"] for t in tasks] == [False, False]


def test_mention_without_declaration_does_not_propagate():
    # 030: 言及ベースの推定は lint に降格。tray のもとでは未宣言の入力は読めないので、
    # needs に無い依存は構造的に存在できない——伝播の根拠にしない。
    tasks = [_task("data.csv"), _task("report.md", task="data.csv を読んで report.md を書く")]
    invalidate(tasks, ["data.csv"])
    assert [t["done"] for t in tasks] == [False, True]


def test_earlier_task_is_not_dragged_in_by_mentioning_a_later_file():
    # 013 の実害: 検査器タスク（前段）が成果物名に言及していたため巻き込まれた。
    # 030 からは構造的に起きない——needs は後ろから前を指す辺であり、逆流する辺が無い。
    tasks = [
        _task("verify.ps1", task="report.md の内容を検査するスクリプトを作る"),
        _task("report.md", needs=["verify.ps1"],
              check={"run": "powershell -File verify.ps1", "expect": "PASS"}),
    ]
    invalidate(tasks, ["report.md"])
    assert tasks[0]["done"] is True   # 検査器は生き残る
    assert tasks[1]["done"] is False


def test_propagation_is_transitive():
    tasks = [_task("a.md"), _task("b.md", needs=["a.md"]), _task("c.md", needs=["b.md"])]
    invalidate(tasks, ["a.md"])
    assert [t["done"] for t in tasks] == [False, False, False]


def test_a_declared_external_file_propagates():
    # 産出タスクがタスク列に無いファイル（外部入力）も、宣言されていれば依存辺になる。
    tasks = [_task("report.md", needs=["external.csv"])]
    invalidate(tasks, ["external.csv"])
    assert tasks[0]["done"] is False


def test_qa_task_is_always_invalidated():
    tasks = [_task("a.md"), _task("verdict.md", role="qa")]
    invalidate(tasks, ["nothing.md"])
    assert tasks[1]["done"] is False   # 検証を飛ばして完遂させない


# --- 失敗の事実の伝達（合意014 A: NG 理由を実行者へ） ---------------------------

def test_task_goal_carries_the_previous_failure():
    # 実行者は「なぜ通らなかったか」を知らされないと、成果物でなく検査器を直しにいく（013 の実害）。
    t = _task("report.md", check={"run": "check.ps1", "expect": "PASS"})
    t["last_failure"] = "  検査: check.ps1\n  期待: PASS\n  実際: FAIL"
    goal = task_goal(t, "SPEC.md")
    assert "前回の失敗" in goal
    assert "実際: FAIL" in goal


def test_task_goal_has_no_failure_section_when_there_is_none():
    goal = task_goal(_task("report.md"), "SPEC.md")
    assert "前回の失敗" not in goal


def test_invalidate_records_the_failure_on_invalidated_tasks():
    # 無効化と同時に「コードが実行した事実」を載せる。載せるのは事実だけ（合意014 ①）。
    tasks = [_task("a.md"), _task("b.md", needs=["a.md"])]
    invalidate(tasks, ["a.md"], failure="  検査: run\n  期待: OK\n  実際: NG")
    assert "実際: NG" in tasks[0]["last_failure"]
    assert "実際: NG" in tasks[1]["last_failure"]   # 巻き込まれた側にも理由が要る


def test_invalidate_without_failure_leaves_the_field_alone():
    tasks = [_task("a.md")]
    tasks[0]["last_failure"] = "古い失敗"
    invalidate(tasks, ["a.md"])
    assert tasks[0]["last_failure"] == "古い失敗"


def test_stale_failure_is_cleared_when_the_task_succeeds():
    # 次の周に古い失敗を持ち越さない（直近1回だけ持つ＝合意014 ②）。
    from mu.process import clear_failure
    t = _task("a.md")
    t["last_failure"] = "前回の失敗"
    clear_failure(t)
    assert t.get("last_failure") is None


# --- 019: 正直な FAIL 判定書は成功である ---------------------------------------
#
# 018 実走: QA が ITEM 3: FAIL と正しく書いたのに、L2 Reflect が「成果物を直せ」と
# 要求し続けた。L2 は criterion（コード供給）に対して判定するので、
# 「FAIL を含む判定書も完成」を criterion と契約の両方に明記する。

from mu.process import normalize_tasks, task_goal


def test_qa_criterion_says_an_honest_fail_verdict_is_complete():
    tasks = normalize_tasks(
        [{"role": "implementer", "task": "作る", "file": "out.txt", "criterion": "ある"}],
        {"qa": {}, "implementer": {}}, lambda e: None,
    )
    qa = next(t for t in tasks if t["role"] == "qa")
    assert "FAIL" in qa["criterion"]
    assert "完成" in qa["criterion"]      # FAIL を含む判定書も完成、が成功条件に見える


def test_qa_contract_forbids_fixing_the_deliverable_to_erase_a_fail():
    tasks = normalize_tasks(
        [{"role": "implementer", "task": "作る", "file": "out.txt", "criterion": "ある"}],
        {"qa": {}, "implementer": {}}, lambda e: None,
    )
    qa = next(t for t in tasks if t["role"] == "qa")
    goal = task_goal(qa, "SPEC.md")
    assert "不合格は不合格と書いて完成" in goal


# --- 030: needs — 入力の宣言・ゲート・lint --------------------------------------
#
# 出力（file）だけでなく入力（needs）も宣言される。needs はゲート——満たせなければ
# タスクは実行できない（師匠の定式化）。言及ベースの推定は計画時 lint に降格。
# 出力ファイルの書き手は1ロールに固定（single-writer。師匠宣言）。

from mu.process import write_process


def test_needs_are_normalized_deduped_and_default_empty():
    tasks = normalize_tasks(
        [{"role": "implementer", "task": "作る", "file": "out.txt", "criterion": "ある",
          "needs": [" design.md ", "design.md", "", "data.csv"]},
         {"role": "implementer", "task": "作る", "file": "b.txt", "criterion": "ある"}],
        {"qa": {}, "implementer": {}}, lambda e: None,
    )
    assert tasks[0]["needs"] == ["design.md", "data.csv"]
    assert tasks[1]["needs"] == []


def test_qa_needs_are_supplied_by_code():
    # 床: 検証者が実物を見られないプロセスを作れない。QA の needs は全成果物をコードが供給する。
    tasks = normalize_tasks(
        [{"role": "implementer", "task": "作る", "file": "a.py", "criterion": "ある"},
         {"role": "implementer", "task": "作る", "file": "b.txt", "criterion": "ある"}],
        {"qa": {}, "implementer": {}}, lambda e: None,
    )
    assert tasks[-1]["role"] == "qa"
    assert tasks[-1]["needs"] == ["a.py", "b.txt"]


def test_qa_declared_extra_needs_are_kept():
    # PjM が QA に外部入力（照合対象の原データ等）を足で宣言したら、床に上乗せで残す。
    tasks = normalize_tasks(
        [{"role": "implementer", "task": "作る", "file": "report.md", "criterion": "ある"},
         {"role": "qa", "task": "検証", "file": "verdict.md", "criterion": "ITEM",
          "needs": ["sales.csv"]}],
        {"qa": {}, "implementer": {}}, lambda e: None,
    )
    assert tasks[-1]["needs"] == ["report.md", "sales.csv"]


def test_single_writer_violation_is_linted():
    # 出力の書き手は1ロール固定（師匠宣言）。別ロールが同じファイルを書くプロセスは名指しで可視化。
    events = []
    normalize_tasks(
        [{"role": "implementer", "task": "書く", "file": "report.md", "criterion": "ある"},
         {"role": "researcher", "task": "書き直す", "file": "report.md", "criterion": "ある"}],
        {"qa": {}, "implementer": {}, "researcher": {}}, events.append,
    )
    assert ("single_writer_violation", "report.md", "implementer", "researcher") in events


def test_same_role_revision_chain_is_not_a_violation():
    # 改稿チェーン（027: 同一原稿の連続的修正）は同ロール内の直列として正当。
    events = []
    normalize_tasks(
        [{"role": "writer", "task": "初稿", "file": "story.md", "criterion": "ある"},
         {"role": "writer", "task": "改稿", "file": "story.md", "criterion": "ある",
          "needs": ["story.md"]}],
        {"qa": {}, "implementer": {}, "writer": {}}, events.append,
    )
    assert not [e for e in events if e[0] == "single_writer_violation"]


def test_mentioned_but_undeclared_files_are_linted():
    # 言及推定の新しい居場所: 実行前に「読むつもりなら宣言が要る」を可視化する lint。
    events = []
    normalize_tasks(
        [{"role": "implementer", "task": "a.md を作る", "file": "a.md", "criterion": "ある"},
         {"role": "implementer", "task": "a.md を読んで b.md を書く", "file": "b.md",
          "criterion": "ある"}],
        {"qa": {}, "implementer": {}}, events.append,
    )
    assert ("needs_lint", "b.md", ["a.md"]) in events


def test_declared_or_own_files_are_not_linted():
    events = []
    normalize_tasks(
        [{"role": "implementer", "task": "a.md を作る", "file": "a.md", "criterion": "ある"},
         {"role": "implementer", "task": "a.md を読んで b.md を書く", "file": "b.md",
          "criterion": "ある", "needs": ["a.md"]}],
        {"qa": {}, "implementer": {}}, events.append,
    )
    assert not [e for e in events if e[0] == "needs_lint"]


def test_unmet_needs_lists_missing_external_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "have.csv").write_text("x", encoding="utf-8")
    t = _task("out.md", needs=["have.csv", "missing.csv"], done=False)
    assert unmet_needs(t, {}) == ["missing.csv"]


def test_unmet_needs_trusts_the_producer_flag_over_the_disk():
    # タスク列の中で産出されるファイルは「産出タスクが done か」で判定する（内部依存）。
    # 実在で判定するのは、産出タスクがタスク列に居ない外部ファイルだけ。
    t = _task("out.md", needs=["mid.md"], done=False)
    assert unmet_needs(t, {"mid.md": True}) == []
    assert unmet_needs(t, {"mid.md": False}) == ["mid.md"]


def test_task_goal_references_spec_and_declared_needs():
    goal = task_goal(_task("report.md", needs=["design.md", "sales.csv"]), "SPEC.md")
    assert "SPEC.md, design.md, sales.csv" in goal


def test_process_artifact_shows_needs(tmp_path):
    path = tmp_path / "PROCESS.md"
    write_process(str(path), "目的", [_task("b.md", needs=["a.md", "x.csv"])])
    assert "needs: a.md, x.csv" in path.read_text(encoding="utf-8")


# --- 037 B: ゲートに弾かれたとき、直す道を捨てる道より安くする -------------------

def test_needs_hint_points_at_the_real_file_with_the_same_name(tmp_path, monkeypatch):
    # 035: PjM は `l0.py` を宣言して弾かれ（実体は `mu/l0.py`）、再計画で宣言を捨てた。
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mu").mkdir()
    (tmp_path / "mu" / "l0.py").write_text("x", encoding="utf-8")
    hint = needs_hint(["l0.py"])
    assert "mu/l0.py" in hint


def test_needs_hint_is_silent_when_nothing_matches(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert needs_hint(["nowhere.py"]) == ""


def test_needs_hint_skips_files_produced_by_earlier_tasks(tmp_path, monkeypatch):
    # 内部依存の未充足は「名前の誤り」ではなく「順序」。既存のパスを指させたらグラフが壊れる。
    monkeypatch.chdir(tmp_path)
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "design.md").write_text("前回の残骸", encoding="utf-8")
    assert needs_hint(["design.md"], {"design.md": False}) == ""


def test_needs_hint_ignores_tray_copies(tmp_path, monkeypatch):
    # tray（.mu-work）の写しを指させると、共有空間ではなく他人の作業区画を宣言してしまう。
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".mu-work" / "implementer" / "task-1").mkdir(parents=True)
    (tmp_path / ".mu-work" / "implementer" / "task-1" / "spec.md").write_text("x", encoding="utf-8")
    assert needs_hint(["spec.md"]) == ""
