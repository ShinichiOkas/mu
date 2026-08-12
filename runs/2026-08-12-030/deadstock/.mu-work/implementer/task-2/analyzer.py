import csv
from collections import defaultdict

def load_inventory(filename):
    # returns a dict of {code: {"name": name, "stock": stock}}
    data = {}
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row['商品コード']] = {
                "name": row['商品名'],
                "stock": int(row['在庫数'])
            }
    return data

def load_sales(filename):
    # returns a dict of {code: total_count}
    data = defaultdict(int)
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential case mismatch (e.g., p008 vs P008)
            code = row['商品コード'].upper()
            data[code] += int(row['数量'])
    return data

def load_returns(filename):
    # returns a dict of {code: total_count}
    data = defaultdict(int)
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['商品コード'].upper()
            data[code] += int(row['数量'])
    return data

def analyze():
    inventory = load_inventory('inventory.csv')
    sales = load_sales('sales.csv')
    returns = load_returns('returns.csv')

    deadstock_list = []

    for code, info in inventory.items():
        stock = info['stock']
        name = info['name']
        total_sales = sales.get(code, 0)
        total_returns = returns.get(code, 0)
        
        reason = ""
        is_deadstock = False

        # Condition A: Stock >= 10 and Sales == 0
        if stock >= 10 and total_sales == 0:
            is_deadstock = True
            reason = f"在庫数({stock})が多いが、売上実績なし"
        # Condition B: High return ratio or only returns with some stock
        elif total_returns > 0 and (total_sales < 5 or total_sales == 0):
            is_deadstock = True
            reason = f"返品あり（返品:{total_returns}, 売上:{total_sales}）"

        if is_deadstock:
            # The report must contain "死に筋" and a keyword for reason/basis (e.g., 判断理由)
            # We append the "死に筋" context to the logic or header if needed, but the 
            # prompt asks for a specific format in each line or overall.
            # The spec requires "死に筋" word and "判断理由" keyword somewhere.
            deadstock_list.append({
                "code": code,
                "name": name,
                "stock": stock,
                "reason": reason
            })

    with open('deadstock_report.txt', 'w', encoding='utf-8') as f:
        f.write("--- 死に筋商品分析レポート ---\n")
        f.write("判定基準に基づく「死に筋」商品の抽出結果です。\n\n")
        for item in deadstock_list:
            # Format: 商品コード | 商品名 | 現在の在庫数 | 判断理由
            line = f"{item['code']} | {item['name']} | {item['stock']} | {item['reason']}\n"
            f.write(line)

    print(f"Analysis complete. Found {len(deadstock_list)} items.")
    if len(deadstock_list) > 0:
        print("[Success]")

if __name__ == '__main__':
    analyze()
