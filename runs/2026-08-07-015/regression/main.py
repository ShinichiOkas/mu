import csv
from pathlib import Path

def main():
    # Input files
    inventory_file = 'inventory.csv'
    sales_file = 'sales.csv'
    returns_file = 'returns.csv'
    report_file = 'dead_stock_report.txt'

    # Data storage
    inventory_data = {}  # code -> (name, qty)
    sales_totals = {}    # code -> qty
    returns_totals = {}  # code -> qty

    # Load Inventory
    try:
        with open(inventory_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory_data[row['product_code']] = (row['product_name'], int(row['quantity']))
    except FileNotFoundError:
        return

    # Load Sales
    try:
        with open(sales_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['product_code']
                sales_totals[code] = sales_totals.get(code, 0) + int(row['quantity'])
    except FileNotFoundError:
        pass

    # Load Returns
    try:
        with open(returns_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row['product_code']
                returns_totals[code] = returns_totals.get(code, 0) + int(row['quantity'])
    except FileNotFoundError:
        pass

    dead_stocks = []

    for code, (name, inv_qty) in inventory_data.items():
        net_sales = sales_totals.get(code, 0) - returns_totals.get(code, 0)
        
        cond_a = net_sales <= 0
        cond_b = (inv_qty >= 100) and (net_sales < 20)
        
        reason = ""
        if cond_a and cond_b:
            reason = "Both conditions met"
        elif cond_a:
            reason = "Net Sales is 0 or less"
        elif cond_b:
            reason = "High inventory (>=100) and low net sales (<20)"
        
        if reason:
            dead_stocks.append({
                'code': code,
                'name': name,
                'inv': inv_qty,
                'net': net_sales,
                'reason': reason
            })

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("--- Dead Stock Report ---\n")
        for item in dead_stocks:
            f.write(f"Product Code: {item['code']}\n")
            f.write(f"Product Name: {item['name']}\n")
            f.write(f"Inventory: {item['inv']}\n")
            f.write(f"Net Sales: {item['net']}\n")
            f.write(f"Reason: {item['reason']}\n")
            f.write("-------------------------\n")

if __name__ == "__main__":
    main()
