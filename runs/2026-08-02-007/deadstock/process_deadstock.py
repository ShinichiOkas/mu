import csv
from collections import defaultdict

def process_deadstock():
    # 1. Load inventory (Product Master)
    inventory = []
    try:
        with open('inventory.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory.append(row)
    except FileNotFoundError:
        return

    # 2. Aggregate sales
    sales_totals = defaultdict(int)
    try:
        with open('sales.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Support case-insensitive product codes
                code = row['商品コード'].upper()
                sales_totals[code] += int(row['数量'])
    except FileNotFoundError:
        pass

    # 3. Aggregate returns
    returns_totals = defaultdict(int)
    try:
        with open('returns.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['商品コード'].upper()
                returns_totals[code] += int(row['数量'])
    except FileNotFoundError:
        pass

    # 4. Identify deadstock items
    deadstock_items = []
    for item in inventory:
        code = item['商品コード'].upper()
        name = item['商品名']
        
        sales = sales_totals.get(code, 0)
        returns = returns_totals.get(code, 0)
        net_sales = sales - returns
        
        # Condition: Never sold OR net sales <= 0
        # Note: If sales == 0, then net_sales will be <= 0 (unless returns are negative, which shouldn't happen).
        # The design says: "Sells not appearing in sales.csv" OR "net sales <= 0"
        if code not in sales_totals or net_sales <= 0:
            deadstock_items.append({
                'code': item['商品コード'],
                'name': name,
                'net_sales': net_sales
            })

    # 5. Write report
    with open('deadstock_report.txt', mode='w', encoding='utf-8') as f:
        for item in deadstock_items:
            f.write(f"{item['code']},{item['name']},実質販売数：{item['net_sales']}個\n")

if __name__ == "__main__":
    process_deadstock()
