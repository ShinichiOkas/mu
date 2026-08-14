"""日次レポート。report.render をそのまま使う（既存の呼び出し元 その1）。"""
from report import render

ROWS = [
    ["商品", "数量", "金額"],
    ["ノート", 12, 1200],
    ["ボールペン", 30, 3000],
    ["消しゴム", 5, 400],
]

if __name__ == "__main__":
    print(render(ROWS, "日次売上"))
