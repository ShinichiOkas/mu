import csv
import os

def calculate_net_sales(inventory_file, sales_file, returns_file):
    inventory = {}
    with open(inventory_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            inventory[row['商品コード']] = row['商品名']

    sales_sum = {}
    with open(sales_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['商品コード']
            sales_sum[code] = sales_sum.get(code, 0) + int(row['数量'])

    returns_sum = {}
    with open(returns_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['商品コード']
            returns_sum[code] = returns_sum.get(code, 0) + int(row['数量'])

    results = []
    for code, name in inventory.items():
        net_sales = sales_sum.get(code, 0) - returns_sum.get(code, 0)
        results.append((code, name, net_sales))
    
    return results

def generate_report(results, output_file):
    deadstock = [item for item in results if item[2] <= 0]
    with open(output_file, 'w', encoding='utf-8') as f:
        for code, name, net_sales in deadstock:
            f.write(f"[{code}] {name}: 実質売上数量 = {net_sales}\n")

def test_logic():
    # Setup temporary test files
    test_inv = 'test_inventory.csv'
    test_sales = 'test_sales.csv'
    test_returns = 'test_returns.csv'
    test_report = 'test_report.txt'

    try:
        with open(test_inv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['商品コード', '商品名', '在庫数'])
            writer.writerow(['T001', '商品A', '10']) # Net: 10 - 0 = 10 (Keep)
            writer.writerow(['T002', '商品B', '10']) # Net: 5 - 5 = 0 (Dead)
            writer.writerow(['T003', '商品C', '10']) # Net: 0 - 2 = -2 (Dead)
            writer.writerow(['T004', '商品D', '10']) # Net: 0 - 0 = 0 (Dead)

        with open(test_sales, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['日付', '商品コード', '数量'])
            writer.writerow(['2026-01-01', 'T001', '10'])
            writer.writerow(['2026-01-01', 'T002', '5'])

        with open(test_returns, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['日付', '商品コード', '数量'])
            writer.writerow(['2026-01-02', 'T002', '5'])
            writer.writerow(['2026-01-02', 'T003', '2'])

        results = calculate_net_sales(test_inv, test_sales, test_returns)
        generate_report(results, test_report)

        with open(test_report, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verify expectations
        # T001 should NOT be in report
        # T002, T003, T004 should be in report
        assert '[T001]' not in content
        assert '[T002] 商品B: 実質売上数量 = 0' in content
        assert '[T003] 商品C: 実質売上数量 = -2' in content
        assert '[T004] 商品D: 実質売上数量 = 0' in content
        
        print("TEST_PASSED")

    finally:
        # Cleanup
        for f in [test_inv, test_sales, test_returns, test_report]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    test_logic()
