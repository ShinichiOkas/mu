import csv
from datetime import datetime, timedelta

def load_csv(path):
    data = []
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        pass
    return data

def main():
    # 1. Data Loading
    inventory_data = load_csv('inventory.csv')
    sales_data = load_csv('sales.csv')
    returns_data = load_csv('returns.csv')

    # Mapping for inventory: Product ID -> Product Name
    # Headers based on provided files: 商品コード, 商品名, 在庫数
    inventory_map = {row['商品コード']: row['商品名'] for row in inventory_data}
    all_product_ids = list(inventory_map.keys())

    # 2. Time Filtering
    # Identify reference date (max date in sales and returns)
    dates = []
    for row in sales_data:
        dates.append(datetime.strptime(row['日付'], '%Y-%m-%d'))
    for row in returns_data:
        dates.append(datetime.strptime(row['日付'], '%Y-%m-%d'))
    
    if not dates:
        return # Or handle as error

    reference_date = max(dates)
    start_date = reference_date - timedelta(days=90)

    # 3. Aggregation
    # Case-insensitive Product ID handling if needed, but design says "Product ID"
    # Looking at sales.csv, some IDs are lowercase (p008). Let's normalize to uppercase.
    sales_sum = {}
    for row in sales_data:
        date = datetime.strptime(row['日付'], '%Y-%m-%d')
        if start_date <= date <= reference_date:
            pid = row['商品コード'].upper()
            sales_sum[pid] = sales_sum.get(pid, 0) + int(row['数量'])

    returns_sum = {}
    for row in returns_data:
        date = datetime.strptime(row['日付'], '%Y-%m-%d')
        if start_date <= date <= reference_date:
            pid = row['商品コード'].upper()
            returns_sum[pid] = returns_sum.get(pid, 0) + int(row['数量'])

    # 4. Joining & Calculation
    deadstock = []
    for pid in all_product_ids:
        # Normalize pid for lookup
        norm_pid = pid.upper()
        s = sales_sum.get(norm_pid, 0)
        r = returns_sum.get(norm_pid, 0)
        net_sales = s - r
        
        if net_sales == 0:
            deadstock.append({
                'Product ID': pid,
                'Product Name': inventory_map[pid],
                'Net Sales': net_sales
            })

    # 6. Report Generation
    with open('deadstock_report.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Product ID', 'Product Name', 'Net Sales'])
        writer.writeheader()
        writer.writerows(deadstock)

    print(f"[SUMMARY] Processed: {len(all_product_ids)} products, Deadstock identified: {len(deadstock)} products.")

if __name__ == "__main__":
    main()
