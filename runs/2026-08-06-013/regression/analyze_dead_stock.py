import csv
from collections import defaultdict

def analyze_dead_stock():
    inventory = {}
    with open('inventory.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['商品コード']
            inventory[code] = {
                'name': row['商品名'],
                'stock': int(row['在庫数'])
            }

    sales_totals = defaultdict(int)
    with open('sales.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle potential case inconsistency in product codes (e.g., p008 vs P008)
            code = row['商品コード'].upper()
            sales_totals[code] += int(row['数量'])

    returns_totals = defaultdict(int)
    with open('returns.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['商品コード'].upper()
            returns_totals[code] += int(row['数量'])

    dead_stock_list = []
    
    # Iterate over all products in inventory to identify dead stock
    for code, info in inventory.items():
        # Ensure we use uppercase for consistency when looking up sales/returns
        lookup_code = code.upper()
        net_sales = sales_totals[lookup_code] - returns_totals[lookup_code]
        stock = info['stock']
        
        is_dead_stock = False
        if net_sales <= 0:
            is_dead_stock = True
        elif stock > 0 and (net_sales / stock) < 0.1:
            is_dead_stock = True
        elif stock == 0 and net_sales <= 0:
            is_dead_stock = True

        if is_dead_stock:
            dead_stock_list.append({
                'code': code,
                'name': info['name'],
                'stock': stock,
                'net_sales': net_sales
            })

    with open('dead_stock_report.txt', 'w', encoding='utf-8') as f:
        f.write("死に筋商品レポート\n")
        f.write("====================\n")
        if not dead_stock_list:
            f.write("死に筋商品は検出されませんでした。\n")
        else:
            for item in dead_stock_list:
                f.write(f"商品コード: {item['code']}, 商品名: {item['name']}\n")
                f.write(f"判定根拠: 在庫数={item['stock']}, 純売上数={item['net_sales']}\n")
                f.write("--------------------\n")

if __name__ == "__main__":
    analyze_dead_stock()
