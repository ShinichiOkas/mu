"""判定書の項目別読み取りと集約（合意017）。

完遂判定を LLM の総合判断（ACHIEVED: yes|no）から、**項目ごとの二値をコードが集約する**形に
変える。LLM は点数付けのようなスカラー量が苦手で、「全体としてどうか」を問うと寛容側に倒れる
——012 では決定論 check が 3件中2件 NG なのに QA は yes と書いた。
項目ごとに「この項目の証拠が成果物の中にあるか」に還元すれば、judge の設計と噛み合う。
"""

from mu.process import read_verdict

CRITERIA = [
    {"text": "4ツールすべての記載", "run": "", "expect": ""},
    {"text": "各主張に出典 URL", "run": "", "expect": ""},
    {"text": "結論の明記", "run": "", "expect": ""},
]


def _tasks(tmp_path, body):
    p = tmp_path / "verdict.md"
    p.write_text(body, encoding="utf-8")
    return [{"role": "qa", "file": str(p), "done": True}]


def test_all_items_pass_means_achieved(tmp_path):
    tasks = _tasks(tmp_path, (
        "ITEM 1: PASS — 表に4ツールが並んでいる\n"
        "ITEM 2: PASS — 各節に URL がある\n"
        "ITEM 3: PASS — 「Ollama を使い続けるべき」と明記\n"
        "GAP:\n"
    ))
    v = read_verdict(tasks, CRITERIA)
    assert v["achieved"] == "yes"
    assert [i["verdict"] for i in v["items"]] == ["pass", "pass", "pass"]


def test_one_fail_blocks_completion(tmp_path):
    # 10個なら10個 PASS。部分達成を完成と呼ばない（合意017 ③）。
    tasks = _tasks(tmp_path, (
        "ITEM 1: PASS — ある\n"
        "ITEM 2: FAIL — 3件の主張に出典が無い\n"
        "ITEM 3: PASS — ある\n"
    ))
    v = read_verdict(tasks, CRITERIA)
    assert v["achieved"] == "no"
    assert v["items"][1]["verdict"] == "fail"
    assert "出典が無い" in v["items"][1]["evidence"]


def test_uncertain_is_not_a_pass(tmp_path):
    # PASS でなければ未達（合意017 ②）。ただし FAIL（未達と分かった）と
    # UNCERTAIN（判定できなかった）は上位の判断が変わるので、値でも区別する。
    tasks = _tasks(tmp_path, (
        "ITEM 1: PASS — ある\n"
        "ITEM 2: UNCERTAIN — 読み取れない\n"
        "ITEM 3: PASS — ある\n"
    ))
    v = read_verdict(tasks, CRITERIA)
    assert v["achieved"] == "uncertain"      # 達成ではない（yes ではない）
    assert v["items"][1]["verdict"] == "uncertain"
    assert "判定不能" in v["reason"]


def test_fail_dominates_uncertain(tmp_path):
    # FAIL が1つでもあれば「未達」。判定不能に紛れさせない。
    tasks = _tasks(tmp_path, (
        "ITEM 1: FAIL — 無い\nITEM 2: UNCERTAIN — 読めない\nITEM 3: PASS — ある\n"
    ))
    assert read_verdict(tasks, CRITERIA)["achieved"] == "no"


def test_missing_item_is_treated_as_uncertain(tmp_path):
    # 判定書に現れない受入基準を黙って落とすと「書かなければ通る」抜け道になる。
    tasks = _tasks(tmp_path, "ITEM 1: PASS — ある\nITEM 3: PASS — ある\n")
    v = read_verdict(tasks, CRITERIA)
    assert v["achieved"] == "uncertain"   # 達成ではない（書かなければ通る、にはならない）
    assert v["items"][1]["verdict"] == "uncertain"
    assert len(v["items"]) == 3          # 受入基準の数だけ必ず並ぶ


def test_decorated_lines_are_read(tmp_path):
    # 契約はコードが供給するが、書き手は LLM であり装飾へ流れる（既存 verdict 読みと同じ作法）。
    tasks = _tasks(tmp_path, (
        "**ITEM 1:** PASS — ある\n"
        "- ITEM 2: **FAIL** — 足りない\n"
        "ITEM 3 : pass — ある\n"
    ))
    v = read_verdict(tasks, CRITERIA)
    assert [i["verdict"] for i in v["items"]] == ["pass", "fail", "pass"]


def test_verdict_without_any_item_line_is_uncertain(tmp_path):
    # 総合的な言い切り（「全体として良好」）を合格として読まない。
    tasks = _tasks(tmp_path, "全体として良好です。合格とします。")
    v = read_verdict(tasks, CRITERIA)
    assert v["achieved"] == "uncertain"
    assert all(i["verdict"] == "uncertain" for i in v["items"])


def test_a_total_judgement_line_does_not_override_the_items(tmp_path):
    # 総合判断は LLM から取り上げる。ACHIEVED 行を書かれても集約はコードが決める。
    tasks = _tasks(tmp_path, (
        "ACHIEVED: yes\n"
        "ITEM 1: PASS — ある\n"
        "ITEM 2: FAIL — 無い\n"
        "ITEM 3: PASS — ある\n"
    ))
    v = read_verdict(tasks, CRITERIA)
    assert v["achieved"] == "no"


def test_gap_is_still_read(tmp_path):
    tasks = _tasks(tmp_path, "ITEM 1: FAIL — 無い\nGAP: 出典を追加すること\n")
    v = read_verdict(tasks, [CRITERIA[0]])
    assert "出典を追加" in v["gap"]


def test_no_qa_task_still_returns_none(tmp_path):
    assert read_verdict([{"role": "implementer", "file": "x", "done": True}], CRITERIA) is None


def test_missing_verdict_file_is_uncertain(tmp_path):
    tasks = [{"role": "qa", "file": str(tmp_path / "nope.md"), "done": True}]
    v = read_verdict(tasks, CRITERIA)
    assert v["achieved"] == "uncertain"
