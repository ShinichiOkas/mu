import csv
from collections import defaultdict

def process_inventory():
    # Inventory: code -> name
    inventory = {}
    try:
        with open('inventory.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory[row['商品コード']] = row['商品名']
    except FileNotFoundError:
        print("Error: inventory.csv not found")
        return

    # Sales: code -> total quantity
    sales_totals = defaultdict(int)
    try:
        with open('sales.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['商品コード']
                sales_totals[code] += int(row['数量'])
    except FileNotFoundError:
        pass

    # Returns: code -> total quantity
    returns_totals = defaultdict(int)
    try:
        with open('returns.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['商品コード']
                returns_totals[code] += int(row['数量'])
    except FileNotFoundError:
        pass

    # Calculate actual sales and find dead stock
    dead_stock = []
    total_products = len(inventory)
    
    for code, name in inventory.items():
        # Normalize codes to uppercase for matching (based on design/sales.csv observations)
        # Let's find all matches regardless of case
        s_val = 0
        r_val = 0
        
        for scode, sval in sales_totals.items():
            if scode.upper() == code.upper():
                s_val += sval
        for rcode, rval in returns_totals.items():
            if rcode.upper() == code.upper():
                r_val += rval
        
        actual = s_val - r_val
        if actual <= 0:
            # SPEC requires "実質販売数" in the output
            dead_stock.append(f"{name}\n売上合計 {s_val}個 - 返品合計 {r_val}個 = 実質販売数 {actual}個\n")

    # Write report
    with open('dead_stock_report.txt', mode='w', encoding='utf-8') as f:
        f.write('\n'.join(dead_stock))
    
    print(f"[VERIFICATION]: Processed {total_products} products, found {len(dead_stock)} dead stocks.")
    print('REPORT_GENERATED')

if __name__ == '__main__':
    process_inventory()
