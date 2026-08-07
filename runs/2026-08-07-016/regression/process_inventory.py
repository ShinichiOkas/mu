import csv
from collections import defaultdict

def process_inventory():
    # Data structures
    inventory = {} # code -> count
    sales_totals = defaultdict(int)
    returns_totals = defaultdict(int)

    # 1. Load inventory.csv
    try:
        with open('inventory.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory[row['商品コード']] = int(row['在庫数'])
    except FileNotFoundError:
        print("Error: inventory.csv not found")
        return

    # 2. Load sales.csv
    try:
        with open('sales.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Normalize code to uppercase to handle cases like p008
                code = row['商品コード'].upper()
                sales_totals[code] += int(row['数量'])
    except FileNotFoundError:
        print("Error: sales.csv not found")
        return

    # 3. Load returns.csv
    try:
        with open('returns.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['商品コード'].upper()
                returns_totals[code] += int(row['数量'])
    except FileNotFoundError:
        print("Error: returns.csv not found")
        return

    # 4. Identification and Reporting
    dead_stock_list = []
    processed_count = 0

    for code, inv_count in inventory.items():
        processed_count += 1
        # Calculate Net Sales Quantity (正味販売数量)
        # Use .upper() to ensure match with sales/returns totals
        s_qty = sales_totals.get(code.upper(), 0)
        r_qty = returns_totals.get(code.upper(), 0)
        net_sales = s_qty - r_qty

        # Dead stock criteria:
        # - NetSalesQuantity <= 0
        # - OR (NetSalesQuantity > 0 AND InventoryCount >= 100)
        is_dead = False
        reason = ""
        if net_sales <= 0:
            is_dead = True
            reason = "Low sales volume"
        elif inv_count >= 100:
            is_dead = True
            reason = "High inventory level"

        if is_dead:
            dead_stock_list.append({
                'code': code,
                'reason': reason,
                'net_sales': net_sales,
                'inventory': inv_count
            })

    # Write report
    with open('dead_stock_report.txt', mode='w', encoding='utf-8') as f:
        for item in dead_stock_list:
            f.write(f"Product Code: {item['code']}\n")
            f.write(f"Reason: {item['reason']} (Net Sales Quantity: {item['net_sales']}, Inventory: {item['inventory']})\n")
            f.write("-------------------------------------------\n")

    # Execution Marker
    print(f"RESULT: [Processed: {processed_count}, Identified: {len(dead_stock_list)}]")

if __name__ == "__main__":
    process_inventory()
