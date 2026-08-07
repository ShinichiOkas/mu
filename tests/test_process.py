"""mu/process.py（プロセス＝タスク列の facility）のユニットテスト。

ここで守るのは**コードの決定論**の側だけ——無効化の伝播と、タスク goal の組み立て。
判断（どこを無効化するか）は PjM の仕事であり、このモジュールの責務ではない。
"""

from mu.process import invalidate, task_goal


def _task(file, *, role="implementer", task="", criterion="", check=None, done=True):
    t = {"role": role, "task": task or f"{file} を作る", "file": file,
         "criterion": criterion or f"{file} が正しいこと", "done": done}
    if check:
        t["check"] = check
    return t


# --- 無効化の伝播（合意014 B: 逆流を止める） -----------------------------------

def test_named_file_is_invalidated():
    tasks = [_task("a.md"), _task("b.md")]
    invalidate(tasks, ["a.md"])
    assert tasks[0]["done"] is False
    assert tasks[1]["done"] is True


def test_later_task_that_mentions_the_file_is_invalidated():
    # 後続タスクが無効化されたファイルに言及していれば依存とみなす（従来の振る舞い）。
    tasks = [_task("data.csv"), _task("report.md", task="data.csv を読んで report.md を書く")]
    invalidate(tasks, ["data.csv"])
    assert [t["done"] for t in tasks] == [False, False]


def test_earlier_task_is_not_dragged_in_by_mentioning_a_later_file():
    # 013 の実害: 検査器タスク（前段）が成果物名に言及していたため巻き込まれ、
    # PjM が凍結を守る判断（invalidate は成果物のみ）をしていたのにコードが覆した。
    # プロセスは依存順に並ぶ契約なので、**前段は後段に依存しない**。
    tasks = [
        _task("verify.ps1", task="report.md の内容を検査するスクリプトを作る"),
        _task("report.md", check={"run": "powershell -File verify.ps1", "expect": "PASS"}),
    ]
    invalidate(tasks, ["report.md"])
    assert tasks[0]["done"] is True   # 検査器は生き残る
    assert tasks[1]["done"] is False


def test_propagation_is_transitive_forward_only():
    tasks = [_task("a.md"), _task("b.md", task="a.md を使う"), _task("c.md", task="b.md を使う")]
    invalidate(tasks, ["a.md"])
    assert [t["done"] for t in tasks] == [False, False, False]


def test_mention_of_an_unknown_file_still_propagates():
    # タスク列に産出タスクが無いファイル（外部入力など）は、保守的に依存とみなす。
    tasks = [_task("report.md", task="external.csv を読む")]
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
    goal = task_goal(t, "SPEC.md", [])
    assert "前回の失敗" in goal
    assert "実際: FAIL" in goal


def test_task_goal_has_no_failure_section_when_there_is_none():
    goal = task_goal(_task("report.md"), "SPEC.md", [])
    assert "前回の失敗" not in goal


def test_invalidate_records_the_failure_on_invalidated_tasks():
    # 無効化と同時に「コードが実行した事実」を載せる。載せるのは事実だけ（合意014 ①）。
    tasks = [_task("a.md"), _task("b.md", task="a.md を使う")]
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
    goal = task_goal(qa, "SPEC.md", [])
    assert "不合格は不合格と書いて完成" in goal
