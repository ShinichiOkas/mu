import csv
from collections import defaultdict

def process_inventory():
    # Read inventory
    inventory = {}
    try:
        with open('inventory.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory[row['product_code']] = {
                    'name': row['product_name'],
                    'quantity': int(row['quantity'])
                }
    except FileNotFoundError:
        print("inventory.csv not found")
        return

    # Read sales
    sales_counts = defaultdict(int)
    try:
        with open('sales.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sales_counts[row['product_code']] += int(row['quantity'])
    except FileNotFoundError:
        print("sales.csv not found")
        return

    # Read returns
    returns_counts = defaultdict(int)
    try:
        with open('returns.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                returns_counts[row['product_code']] += int(row['quantity'])
    except FileNotFoundError:
        print("returns.csv not found")
        return

    dead_stock_items = []

    for code, info in inventory.items():
        net_sales = sales_counts[code] - returns_counts[code]
        stock = info['quantity']
        name = info['name']
        
        is_dead = False
        reason = ""
        
        if net_sales <= 0:
            is_dead = True
            reason = f"正味販売数({net_sales})が0以下であるため"
        elif stock >= 100 and net_sales < 20:
            is_dead = True
            reason = f"在庫数({stock})が100個以上かつ正味販売数({net_sales})が20個未満であるため"
            
        if is_dead:
            dead_stock_items.append({
                'code': code,
                'name': name,
                'stock': stock,
                'net_sales': net_sales,
                'reason': reason
            })

    with open('dead_stock_report.txt', mode='w', encoding='utf-8') as f:
        f.write("死に筋商品報告書\n")
        f.write("====================\n")
        for item in dead_stock_items:
            f.write(f"商品コード: {item['code']}\n")
            f.write(f"商品名: {item['name']}\n")
            f.write(f"在庫数: {item['stock']}\n")
            f.write(f"正味販売数: {item['net_sales']}\n")
            f.write(f"判定理由: {item['reason']}\n")
            f.write("--------------------\n")

if __name__ == "__main__":
    process_inventory()
