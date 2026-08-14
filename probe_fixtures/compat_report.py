"""表形式レポートの整形。

    render(rows, title) -> str

`rows` は「1行目が見出し、2行目以降がデータ」の2次元リスト。
数値だけの列は右寄せ、それ以外は左寄せ。最下段に合計行を必ず付ける。
"""

TOTAL_LABEL = "合計"
COLUMN_GAP = "  "
RULE_CHAR = "-"
TITLE_RULE_CHAR = "="


def is_number(value):
    """セルが数値として扱えるか（int/float、または数字だけの文字列）。"""
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    text = str(value).strip()
    if not text:
        return False
    if text.startswith("-"):
        text = text[1:]
    return text.replace(".", "", 1).isdigit()


def cell_text(value):
    """セルを文字列にする。float は小数第1位まで、それ以外はそのまま。"""
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def numeric_columns(rows):
    """データ行がすべて数値である列の番号（0 起点）を返す。"""
    if len(rows) < 2:
        return []
    width = len(rows[0])
    out = []
    for col in range(width):
        values = [row[col] for row in rows[1:] if col < len(row)]
        if values and all(is_number(v) for v in values):
            out.append(col)
    return out


def total_row(rows):
    """合計行を作る。数値列は合計、先頭列はラベル、それ以外は空。"""
    numerics = numeric_columns(rows)
    cells = []
    for col in range(len(rows[0])):
        if col == 0 and col not in numerics:
            cells.append(TOTAL_LABEL)
        elif col in numerics:
            total = sum(float(row[col]) for row in rows[1:] if col < len(row))
            cells.append(int(total) if float(total).is_integer() else round(total, 1))
        else:
            cells.append("")
    return cells


def column_widths(rows):
    """各列の表示幅（見出し・データ・合計行のうち最長）。"""
    all_rows = list(rows) + [total_row(rows)]
    widths = []
    for col in range(len(rows[0])):
        widths.append(max(len(cell_text(row[col])) for row in all_rows if col < len(row)))
    return widths


def format_row(cells, widths, numerics):
    """1行を幅に合わせて整える（数値列は右寄せ）。"""
    parts = []
    for col, cell in enumerate(cells):
        text = cell_text(cell)
        parts.append(text.rjust(widths[col]) if col in numerics else text.ljust(widths[col]))
    return COLUMN_GAP.join(parts).rstrip()


def rule(widths):
    """区切り線を作る。"""
    return COLUMN_GAP.join(RULE_CHAR * w for w in widths)


def render(rows, title):
    """表を文字列にする。"""
    if not rows:
        raise ValueError("rows が空である")
    numerics = numeric_columns(rows)
    widths = column_widths(rows)
    lines = [title, TITLE_RULE_CHAR * len(rule(widths)),
             format_row(rows[0], widths, []),
             rule(widths)]
    for row in rows[1:]:
        lines.append(format_row(row, widths, numerics))
    lines.append(rule(widths))
    lines.append(format_row(total_row(rows), widths, numerics))
    return "\n".join(lines)
