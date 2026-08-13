"""probe_learning（L6 診断の単体測定・合意033）の決定論部分のテスト。

測るのは LLM ではなく計器——台帳のロード・材料の抽出・条件 R/N の組み立てが
設計どおりであること。初回測定（B）の法医学で判明した計器の欠陥への対処（B2）を
床として固定する: **検証済み gold**（決定的証拠が生ログに実在し、材料に生存する）・
**優先度充填**（位置でなく種類で残す）・**gold の複数化**・**目的の注入**。
リークの床（答えを含む記録を材料にしない）も引き続きここで固定する。
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


def test_every_case_points_at_a_real_log_and_known_golds():
    ledger = load_ledger()
    for name, case in CASES.items():
        assert (REPO / case["log"]).is_file(), f"{name}: 生ログが無い {case['log']}"
        for g in case["golds"]:
            assert g in ledger, f"{name}: gold が台帳に無い {g}"
        assert case["log"].endswith(".log"), f"{name}: 材料は生ログのみ（README はリーク）"


def test_gold_evidence_exists_in_the_log_and_survives_into_the_material():
    # B の法医学で判明した欠陥への床: gold は物語からでなく**ログの実在の証拠**から貼る。
    # (a) 生ログに実在 (b) thick 材料に生存——生存しないなら測定は公平でない。
    for name, case in CASES.items():
        raw = case_text(case)
        thick = materials(raw, "thick")
        for marker in case["evidence"]:
            assert marker in raw, f"{name}: 証拠が生ログに無い（gold 未検証）: {marker}"
            assert marker in thick, f"{name}: 証拠が材料で失われた（切り捨ての欠陥）: {marker}"


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


def test_priority_fill_keeps_late_control_lines_over_early_chatter():
    # B2 の中身: 位置切り（中央省略）をやめ、種類で残す。上限を大きく超えるログの
    # **末尾近くの制御面の行**（検査・拒否）が、序盤の雑談的な実況より優先して生き残る。
    chatter = "\n".join(f"      [L3] 単位 {i} の何気ない実況テキストがここに続く" for i in range(3000))
    log = chatter + "\n   [L4] 検査[NG] 決定的な証拠 :: expected marker not found\n"
    text = materials(log, "thick")
    assert "決定的な証拠" in text                  # 末尾の制御面が残る
    assert "（…省略" in text                       # 落とした行は数を明示（黙って切らない）
    assert len(text) <= 62_000


def test_condition_n_removes_every_gold_of_the_case():
    ledger = load_ledger()
    golds = CASES["grounding-drop"]["golds"]
    assert len(golds) == 2                         # 根因と近因の併存（B の法医学の帰結）
    lines_n = ledger_lines(ledger, exclude=tuple(golds))
    for g in golds:
        assert g not in lines_n
    assert lines_n.count("- ") == len(ledger) - 2


def test_grounding_drop_case_shows_only_round_zero():
    text = case_text(CASES["grounding-drop"])
    assert "=== R0 ===" in text
    assert "=== R1 ===" not in text     # 後続周は同じ失敗の繰り返し＝答えのリーク


def test_purpose_is_injected_when_the_log_lacks_it():
    # 020 のログには目的の原文が印字されていない——∀→∃ は両側が揃わないと診断不能。
    # その走が実際に受け取った目的を材料の先頭に添える（診断の答えは含まない）。
    ledger = load_ledger()
    _, user = build_input(CASES["quantifier"], "thin", "R", ledger)
    assert "必ず出典" in user                       # ∀ の側（注入された目的）
    assert "記述されていること" in user              # ∃ の側（ログ由来の受入基準）
    assert "PURPOSE (the goal this run actually received" in user


def test_learner_input_carries_ledger_record_and_contract():
    ledger = load_ledger()
    system, user = build_input(CASES["regenerate-loss"], "thick", "R", ledger)
    assert "MECHANICAL CAUSE" in system            # やり方は roles/learner.md から
    assert "Reply as JSON" in system               # 形はスキーマから（コード供給）
    assert "LEDGER (known failure modes):" in user
    assert "RUN RECORD" in user
