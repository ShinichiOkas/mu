import csv
from collections import defaultdict

def main():
    # Read inventory to get all product codes and names
    inventory = {}
    try:
        with open('inventory.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory[row['商品コード']] = row['商品名']
    except FileNotFoundError:
        print("Error: inventory.csv not found.")
        return

    # Calculate total sales per item
    sales_count = defaultdict(int)
    try:
        with open('sales.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize product code to uppercase
                code = row['商品コード'].upper()
                sales_count[code] += int(row['数量'])
    except FileNotFoundError:
        print("Error: sales.csv not found.")
        return

    # Calculate total returns per item
    returns_count = defaultdict(int)
    try:
        with open('returns.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize product code to uppercase
                code = row['商品コード'].upper()
                returns_count[code] += int(row['数量'])
    except FileNotFoundError:
        print("Error: returns.csv not found.")
        return

    # Identify deadstock: net sales (sales - returns) <= 0
    deadstock_items = []
    for code, name in inventory.items():
        net_sales = sales_count[code] - returns_count[code]
        if net_sales <= 0:
            deadstock_items.append((code, name, net_sales))

    # Write report
    try:
        with open('deadstock_report.txt', mode='w', encoding='utf-8') as f:
            f.write("死に筋商品リスト\n")
            f.write("判定基準: 純販売数 (販売数 - 返品数) が 0 以下の商品\n")
            f.write("-" * 30 + "\n")
            if not deadstock_items:
                f.write("該当なし\n")
            else:
                for code, name, net_sales in deadstock_items:
                    f.write(f"{code}: {name} (純販売数: {net_sales})\n")
    except Exception as e:
        print(f"Error writing report: {e}")

if __name__ == "__main__":
    main()
