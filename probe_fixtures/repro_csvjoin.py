"""顧客別の売上集計。

    python csvjoin.py

customers.csv と orders.csv を突き合わせ、顧客ごとの合計金額と注文件数を
report.csv に書き出す。注文が1件も無い顧客も、合計 0 の行として必ず出す。
"""

import csv
import sys
from pathlib import Path

CUSTOMERS = "customers.csv"
ORDERS = "orders.csv"
REPORT = "report.csv"
REPORT_COLUMNS = ("customer_id", "name", "region", "total", "orders")


def read_rows(path):
    """CSV を dict の列として読む。ファイルが無ければ空。"""
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def clean(value):
    """前後の空白と、Excel 由来の全角空白を落とす。"""
    return str(value or "").strip().replace("　", "")


def to_amount(value):
    """金額を数値にする。空欄や壊れた値は 0 として扱う（欠損は集計から落とさない）。"""
    text = clean(value)
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def build_customers(rows):
    """顧客表を id 引きの辞書にする。"""
    table = {}
    for row in rows:
        cid = clean(row.get("customer_id"))
        if not cid:
            continue
        table[cid] = {
            "customer_id": cid,
            "name": clean(row.get("name")),
            "region": clean(row.get("region")),
        }
    return table


def accumulate(orders, customers):
    """注文を顧客ごとに足し上げる。

    顧客表に無い customer_id の注文は、集計から除外する
    （退会済みや試験用データが混ざることがあるため）。
    """
    totals = {cid: 0.0 for cid in customers}
    counts = {cid: 0 for cid in customers}
    for row in orders:
        cid = clean(row.get("customer_id"))
        if cid not in totals:
            continue
        totals[cid] += to_amount(row.get("amount"))
        counts[cid] += 1
    return totals, counts


def build_report(customers, totals, counts):
    """report.csv に書く行を、顧客表の順に組み立てる。"""
    out = []
    for cid, info in customers.items():
        total = totals.get(cid, 0.0)
        out.append({
            "customer_id": cid,
            "name": info["name"],
            "region": info["region"],
            "total": int(total) if float(total).is_integer() else round(total, 2),
            "orders": counts.get(cid, 0),
        })
    return out


def write_report(path, rows):
    """report.csv を書き出す。"""
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(REPORT_COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


def main():
    customers = build_customers(read_rows(CUSTOMERS))
    orders = read_rows(ORDERS)
    if not customers:
        print("CSVJOIN NG customers.csv が読めない")
        return 1
    totals, counts = accumulate(orders, customers)
    rows = build_report(customers, totals, counts)
    written = write_report(REPORT, rows)
    print(f"CSVJOIN OK {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
