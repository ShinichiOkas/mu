import csv
from datetime import datetime, timedelta
from collections import defaultdict

def calculate_deadstock():
    # Constants
    DAYS_WINDOW = 90
    INPUT_INVENTORY = 'inventory.csv'
    INPUT_SALES = 'sales.csv'
    INPUT_RETURNS = 'returns.csv'
    OUTPUT_FILE = 'deadstock_report.csv'
    
    # Current date for filtering (as per design.md)
    current_date = datetime.now()
    start_date = current_date - timedelta(days=DAYS_WINDOW)
    
    # To store net sales calculations
    # key: product_id, value: net_quantity
    net_sales = defaultdict(int)
    
    # Track all product IDs from inventory to ensure we consider products with 0 sales/returns
    products_master = {} # id: name
    
    # 1. Load Inventory (Master)
    try:
        with open(INPUT_INVENTORY, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row['商品コード']
                name = row['商品名']
                products_master[pid] = name
                net_sales[pid] = 0 # Initialize all products with 0 net sales
    except FileNotFoundError:
        print(f"Error: {INPUT_INVENTORY} not found.")
        return

    # Helper to parse date
    def parse_date(date_str):
        return datetime.strptime(date_str, '%Y-%m-%d')

    # 2. Process Sales
    try:
        with open(INPUT_SALES, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = parse_date(row['日付'])
                if date >= start_date and date <= current_date:
                    pid = row['商品コード'].upper() # Handle case sensitivity if necessary
                    # The input files might have mixed case (e.g., p008 in sales.csv)
                    # we should normalize to match inventory.csv if they are the same product
                    # However, inventory.csv has P001... P010. 
                    # Let's try to match by upper case.
                    
                    # Find the original key in products_master that matches pid.upper()
                    actual_pid = next((k for k in products_master if k.upper() == pid), pid)
                    net_sales[actual_pid] += int(row['数量'])
    except FileNotFoundError:
        print(f"Warning: {INPUT_SALES} not found.")

    # 3. Process Returns
    try:
        with open(INPUT_RETURNS, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = parse_date(row['日付'])
                if date >= start_date and date <= current_date:
                    pid = row['商品コード'].upper()
                    actual_pid = next((k for k in products_master if k.upper() == pid), pid)
                    net_sales[actual_pid] -= int(row['数量'])
    except FileNotFoundError:
        print(f"Warning: {INPUT_RETURNS} not found.")

    # 4. Filter Deadstock (Net Sales == 0)
    deadstock_list = []
    for pid, name in products_master.items():
        qty = net_sales[pid]
        if qty == 0:
            deadstock_list.append({
                '商品ID': pid,
                '商品名': name,
                '正味販売数量': qty
            })

    # 5. Export to CSV
    try:
        with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['商品ID', '商品名', '正味販売数量'])
            writer.writeheader()
            writer.writerows(deadstock_list)
    except Exception as e:
        print(f"Error writing to {OUTPUT_FILE}: {e}")

if __name__ == "__main__":
    calculate_deadstock()
