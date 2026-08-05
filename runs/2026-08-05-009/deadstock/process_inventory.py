import csv
import sys
from collections import defaultdict

def main():
    inventory_file = 'inventory.csv'
    sales_file = 'sales.csv'
    returns_file = 'returns.csv'
    report_file = 'report.txt'

    try:
        # Collect inventory items
        inventory = {}
        with open(inventory_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory[row['商品コード']] = row['商品名']

        # Aggregate sales
        sales_counts = defaultdict(int)
        with open(sales_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Product codes might be case-insensitive (e.g., p008 vs P008)
                # Assuming they should match the inventory keys (which are Pxxx)
                code = row['商品コード'].upper()
                sales_counts[code] += int(row['数量'])

        # Aggregate returns
        returns_counts = defaultdict(int)
        with open(returns_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['商品コード'].upper()
                returns_counts[code] += int(row['数量'])

        dead_stock_items = []
        for code, name in inventory.items():
            sales = sales_counts.get(code, 0)
            returns = returns_counts.get(code, 0)
            net_sales = sales - returns
            
            if net_sales <= 0:
                dead_stock_items.append({
                    'code': code,
                    'name': name,
                    'net_sales': net_sales
                })

        with open(report_file, mode='w', encoding='utf-8') as f:
            for item in dead_stock_items:
                f.write(f"[{item['code']}] {item['name']}: 実質売上数量 = {item['net_sales']}\n")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
