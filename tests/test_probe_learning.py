"""probe_learning（L6 診断の単体測定・合意033）の決定論部分のテスト。

測るのは LLM ではなく計器——台帳のロード・材料の抽出・条件 R/N の組み立てが
設計どおりであること。リークの床（答えを含む記録を材料にしない）もここで固定する。
"""

from pathlib import Path

from probe_learning import (
    CASES, build_input, case_text, ledger_lines, load_ledger, materials,
)

REPO = Path(__file__).resolve().parent.parent


def test_ledger_loads_confirmed_entries_with_identity():
    ledger = load_ledger()
    assert len(ledger) >= 10
    for name, doc in ledger.items():
        assert doc.get("description"), name          # 素性（選択・照合の材料）
        assert doc.get("maturity") == "confirmed", name   # seed は承認済み診断のみ
        assert doc.get("name") == name, name         # frontmatter とファイル名の一致


def test_every_case_points_at_a_real_log_and_a_known_gold():
    ledger = load_ledger()
    for name, case in CASES.items():
        assert (REPO / case["log"]).is_file(), f"{name}: 生ログが無い {case['log']}"
        assert case["gold"] in ledger, f"{name}: gold が台帳に無い {case['gold']}"
        assert case["log"].endswith(".log"), f"{name}: 材料は生ログのみ（README はリーク）"


def test_thin_material_drops_tool_lines_and_noise():
    log = ("  [L5] 構造化出力を生成中… (2.6s, 79 tok)\n"
           "        [L1] 思考中（次の行動を決定）… (3.6s, 34 tok)\n"
           "          [tool] write_file(x.md, content=…)\n"
           "       [L2] Reflect（合否）判定中… (1.3s, 104 tok)\n"
           "   [L4] 検査[ok] 基準1 :: exit=0\n")
    thin, thick = materials(log, "thin"), materials(log, "thick")
    assert "[tool]" not in thin and "検査[ok]" in thin and "[L5]" in thin
    assert "[tool]" in thick                      # 機構の証拠は thick にだけ残る
    for text in (thin, thick):
        assert "思考中" not in text and "Reflect（合否）判定中" not in text   # タイミングノイズ


def test_long_material_keeps_head_and_tail_and_says_so():
    log = "\n".join(f"line {i}" for i in range(20_000))
    text = materials(log, "thick")
    assert "line 0" in text and "line 19999" in text     # 冒頭（目的）と末尾（判定）は残す
    assert "中央を省略" in text                            # 黙って切らない


def test_condition_n_removes_only_the_gold_mode():
    ledger = load_ledger()
    lines_r = ledger_lines(ledger)
    lines_n = ledger_lines(ledger, exclude="quantifier-weakening")
    assert "quantifier-weakening" in lines_r
    assert "quantifier-weakening" not in lines_n
    assert lines_n.count("- ") == lines_r.count("- ") - 1   # 抜くのは1件だけ


def test_grounding_drop_case_shows_only_round_zero():
    text = case_text(CASES["grounding-drop"])
    assert "=== R0 ===" in text
    assert "=== R1 ===" not in text     # 後続周は同じ失敗の繰り返し＝答えのリーク


def test_learner_input_carries_ledger_record_and_contract():
    ledger = load_ledger()
    system, user = build_input(CASES["regenerate-loss"], "thick", "R", ledger)
    assert "MECHANICAL CAUSE" in system            # やり方は roles/learner.md から
    assert "Reply as JSON" in system               # 形はスキーマから（コード供給）
    assert "LEDGER (known failure modes):" in user
    assert "RUN RECORD" in user
