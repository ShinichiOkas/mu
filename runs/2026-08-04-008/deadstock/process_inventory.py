import csv
from collections import defaultdict

def process_inventory():
    # Data structures to hold totals
    inventory_data = {}  # {code: (name, stock)}
    sales_totals = defaultdict(int)
    returns_totals = defaultdict(int)

    # Read inventory.csv
    with open('inventory.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['商品コード'].strip()
            inventory_data[code] = (row['商品名'].strip(), int(row['在庫数']))

    # Read sales.csv
    with open('sales.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert code to uppercase to be consistent with inventory.csv
            code = row['商品コード'].strip().upper()
            sales_totals[code] += int(row['数量'])

    # Read returns.csv
    with open('returns.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['商品コード'].strip().upper()
            returns_totals[code] += int(row['数量'])

    deadstock_list = []

    # Process each item in inventory
    for code, (name, stock) in inventory_data.items():
        net_sales = sales_totals[code] - returns_totals[code]
        
        is_deadstock = False
        reason = ""

        if net_sales <= 0:
            is_deadstock = True
            reason = "純売上数が0以下のため"
        elif stock > 0 and net_sales < 10:
            is_deadstock = True
            reason = "純売上数が10個未満のため"

        if is_deadstock:
            deadstock_list.append({
                'code': code,
                'name': name,
                'stock': stock,
                'net_sales': net_sales,
                'reason': reason
            })

    # Write report
    with open('deadstock_report.txt', mode='w', encoding='utf-8', newline='') as f:
        # Writing header (though example showed CSV-like format, the spec mentions columns)
        # Spec says: "項目: 商品コード, 商品名, 在庫数, 純売上数, 判定理由"
        f.write("商品コード,商品名,在庫数,純売上数,判定理由\n")
        for item in deadstock_list:
            line = f"{item['code']},{item['name']},{item['stock']},{item['net_sales']},{item['reason']}\n"
            f.write(line)

if __name__ == "__main__":
    process_inventory()
