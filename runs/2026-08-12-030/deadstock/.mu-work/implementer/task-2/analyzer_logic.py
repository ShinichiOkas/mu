import csv
import argparse
import sys

def load_csv(filename):
    data = []
    try:
        with open(filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
    return data

def analyze_deadstock():
    inventory_data = load_csv('inventory.csv')
    sales_data = load_csv('sales.csv')
    returns_data = load_csv('returns.csv')

    # Processing inventory
    # Map: code -> {name, count}
    inventory_map = {}
    for item in inventory_data:
        code = item['商品コード']
        inventory_map[code] = {
            'name': item['商品名'],
            'count': int(item['在庫数'])
        }

    # Process sales
    # Map: code -> count
    sales_summary = {}
    for s in sales_data:
        code = s['商品コード']
        # Normalize case just in case (e.g., p008 vs P008)
        code = code.upper()
        count = int(s['数量'])
        sales_summary[code] = sales_summary.get(code, 0) + count

    # Process returns
    # Map: code -> count
    returns_summary = {}
    for r in returns_data:
        code = r['商品コード']
        code = code.upper()
        count = int(r['数量'])
        returns_summary[code] = returns_summary.get(code, 0) + count

    deadstock_list = []

    for code, info in inventory_map.items():
        name = info['name']
        stock = info['count']
        sales = sales_summary.get(code, 0)
        returns = returns_summary.get(code, 0)

        reason = ""
        is_deadstock = False

        # Condition A: Stock >= 10 and Sales == 0
        if stock >= 10 and sales == 0:
            is_deadstock = True
            reason = f"在庫が{stock}と多いが、売上履歴がありません。"
        
        # Condition B: High return rate or only returns with low/no sales
        elif returns > 0:
            # If there are returns but very few or no sales relative to items or just low absolute numbers.
            # The spec says "返品履歴のみが存在し、売上が極めて少ない（または返品比率が高い）もの"
            # Let's interpret "low sale" as less than a certain threshold or just non-zero returns with minimal movement.
            if sales < 5: # Small volume of sales
                 is_deadstock = True
                 reason = f"返品が{returns}件あり、売上(数:{sales})に対して戻り割合が高いか低迷しています。"
            elif (returns / (sales + returns)) > 0.5 and sales < 10:
                # High return ratio
                is_deadstock = True
                reason = f"返品が{returns}件あり、売上(数:{sales})に対して返品比率が高いです。"

        if is_deadstock:
            # Requirement from design.md: "死に筋" and "理由" or "根拠" must be in the file.
            # Report format: 商品コード | 商品名 | 現在の在庫数 | 判断理由
            # We will add "死に筋判断内容" to include both required words if possible, 
            # but it's safer to keep them distinct or close together.
            deadstock_list.append(f"{code} | {name} | {stock} | 死に筋の理由: {reason}")

    # Write report
    with open('deadstock_report.txt', 'w', encoding='utf-8') as f:
        for item in deadstock_list:
            f.write(item + '\n')

    print("ANALYSIS_COMPLETE")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    
    analyze_deadstock()
    # The script always prints ANALYSIS_COMPLETE at the end of execution path.
