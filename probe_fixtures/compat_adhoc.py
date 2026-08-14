"""臨時集計。title をキーワード引数で渡し、先頭列が数値の表を描く（既存の呼び出し元 その3）。"""
from report import render

ROWS = [
    ["年", "件数"],
    [2024, 130],
    [2025, 98],
    [2026, 7],
]

if __name__ == "__main__":
    print(render(ROWS, title="年別の件数"))
