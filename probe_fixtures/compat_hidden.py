"""HB compat の隠し検査（probe の持ち物。mu には渡さない）。

既存の呼び出し元の出力が**1バイトも変わっていないこと**は probe 側が
「元の実装で走らせた出力」と突き合わせて測る（この scriptの外）。
ここで測るのは、足すよう頼んだ2つのオプションの振る舞いと、署名の後方互換である。
"""
import inspect
import sys

RESULTS = []


def check(claim, fn):
    try:
        RESULTS.append((True, claim, fn() or "ok"))
    except Exception as e:                       # noqa: BLE001
        RESULTS.append((False, claim, f"{type(e).__name__}: {e}"))


def eq(actual, expected):
    if actual != expected:
        raise AssertionError(f"期待 {expected} / 実際 {actual}")
    return f"= {expected}"


ROWS = [
    ["商品", "数量", "金額"],
    ["ノート", 1200, 1234567],
    ["ペン", 30, 4500],
]

try:
    import report
except Exception as e:                           # noqa: BLE001
    print(f"AUDIT NG report が import できない :: {type(e).__name__}: {e}")
    sys.exit(1)


def body_lines(text):
    """データ行と合計行（表題・罫線・見出し行を除く）。

    見出し行を外すのは、末尾列が左寄せで rstrip される＝行長で幅を測れないため。
    データ行と合計行は末尾列が数値（右寄せ）なので、行長がそのまま総幅になる。
    """
    rows = [ln for ln in text.splitlines()[2:] if set(ln.strip()) - set("- ")]
    return rows[1:]


def base():
    return report.render(ROWS, "検査")


check("render(rows, title) が位置引数2つで呼べる（後方互換）",
      lambda: eq(isinstance(base(), str), True))
check("render の第1・第2引数名が rows / title のまま",
      lambda: eq(list(inspect.signature(report.render).parameters)[:2], ["rows", "title"]))
check("thousands=True で3桁区切りになる",
      lambda: eq("1,234,567" in report.render(ROWS, "検査", thousands=True), True))
check("thousands=True で区切り無しの表記が残らない",
      lambda: eq("1234567" in report.render(ROWS, "検査", thousands=True), False))
check("thousands=True でも合計は正しい（1,239,067）",
      lambda: eq("1,239,067" in report.render(ROWS, "検査", thousands=True), True))
check("thousands の既定は False（既存の出力と同じ）",
      lambda: eq(report.render(ROWS, "検査"), base()))
check("min_width で全列がその幅以上になる",
      lambda: eq(all(len(ln) >= 3 * 10 + 2 * 2 for ln in body_lines(
          report.render(ROWS, "検査", min_width=10))), True))
check("min_width の既定は None（既存の出力と同じ）",
      lambda: eq(report.render(ROWS, "検査", min_width=None), base()))
check("min_width が自然幅より小さいときは自然幅のまま",
      lambda: eq(report.render(ROWS, "検査", min_width=1), base()))
check("2つのオプションは同時に効く",
      lambda: eq("1,234,567" in report.render(ROWS, "検査", min_width=12, thousands=True)
                 and all(len(ln) >= 3 * 12 + 2 * 2 for ln in body_lines(
                     report.render(ROWS, "検査", min_width=12, thousands=True))), True))

for ok, claim, detail in RESULTS:
    print(f"AUDIT {'ok' if ok else 'NG'} {claim} :: {detail}")
sys.exit(0 if all(r[0] for r in RESULTS) else 1)
