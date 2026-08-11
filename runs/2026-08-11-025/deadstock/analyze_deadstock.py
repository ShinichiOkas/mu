import csv
from collections import defaultdict

def analyze_deadstock():
    # 1. 商品マスター抽出
    inventory = {}
    try:
        with open('inventory.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory[row['商品コード']] = row['商品名']
    except Exception as e:
        print(f"Error reading inventory.csv: {e}")
        return False

    # 2. 売上集計
    sales_totals = defaultdict(int)
    try:
        with open('sales.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 商品コードを大文字に統一して集計
                code = row['商品コード'].upper()
                sales_totals[code] += int(row['数量'])
    except Exception as e:
        print(f"Error reading sales.csv: {e}")
        return False

    # 3. 返品集計
    returns_totals = defaultdict(int)
    try:
        with open('returns.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['商品コード'].upper()
                returns_totals[code] += int(row['数量'])
    except Exception as e:
        print(f"Error reading returns.csv: {e}")
        return False

    # 4. 判定
    deadstock_items = []
    # 全商品コードを対象に判定を行う
    for code, name in inventory.items():
        # inventory.csv のコードも大文字として扱う
        code_upper = code.upper()
        net_sales = sales_totals[code_upper] - returns_totals[code_upper]
        if net_sales <= 0:
            deadstock_items.append((code, name, net_sales))

    # 5. 出力
    try:
        with open('deadstock_report.txt', mode='w', encoding='utf-8') as f:
            f.write('死に筋商品リスト\n')
            for code, name, net_sales in deadstock_items:
                f.write(f'商品コード: {code}, 商品名: {name}, 純売上数量: {net_sales}\n')
    except Exception as e:
        print(f"Error writing report: {e}")
        return False

    return True

if __name__ == "__main__":
    if analyze_deadstock():
        print("True")
    else:
        print("False")
