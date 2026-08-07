import csv
import os
import subprocess
from pathlib import Path

def create_test_csvs(inventory_data, sales_data, returns_data):
    """Generates the input CSV files for the system."""
    with open('inventory.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['product_code', 'product_name', 'quantity'])
        writer.writerows(inventory_data)

    with open('sales.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['product_code', 'quantity'])
        writer.writerows(sales_data)

    with open('returns.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['product_code', 'quantity'])
        writer.writerows(returns_data)

def run_report_script():
    """Runs the main script. Searches for a likely report generation script."""
    # List of potential implementation filenames
    potential_scripts = ['main.py', 'report.py', 'dead_stock.py']
    
    # First, check for specifically named potential scripts
    for script in potential_scripts:
        if os.path.exists(script):
            try:
                print(f"Running {script}...")
                subprocess.run(['python', script], check=True, capture_output=True)
                return
            except subprocess.CalledProcessError as e:
                print(f"Error running {script}: {e}")
                return

    # Fallback: any .py file that isn't this test file
    files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'test_inventory.py']
    if not files:
        print("No implementation script found (e.g., main.py, report.py).")
        return
    
    script_to_run = files[0]
    try:
        print(f"Running {script_to_run}...")
        subprocess.run(['python', script_to_run], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running implementation script {script_to_run}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def verify_report(expected_dead_stocks):
    """
    Verifies dead_stock_report.txt against expected dead stocks.
    expected_dead_stocks: list of dicts { 'code': ..., 'reason': ... }
    """
    report_path = Path('dead_stock_report.txt')
    if not report_path.exists():
        print("FAIL: dead_stock_report.txt was not created.")
        return False

    content = report_path.read_text(encoding='utf-8')
    
    # Check if all expected dead stocks are present
    for item in expected_dead_stocks:
        if item['code'] not in content:
            print(f"FAIL: Product {item['code']} should be in the report.")
            return False
        if item['reason'] not in content:
            print(f"FAIL: Reason '{item['reason']}' for product {item['code']} not found.")
            return False

    return True

def test_case_1():
    """
    Test Case 1: Mixed scenario
    P001: Net Sales = 10 - 2 = 8. Inventory 50. (Not Dead Stock)
    P002: Net Sales = 5 - 5 = 0. Inventory 10. (Dead Stock: Condition A)
    P003: Net Sales = 15 - 0 = 15. Inventory 120. (Dead Stock: Condition B)
    P004: Net Sales = 2 - 5 = -3. Inventory 150. (Dead Stock: Both)
    """
    print("Running Test Case 1...")
    inventory = [
        ['P001', 'Widget A', '50'],
        ['P002', 'Widget B', '10'],
        ['P003', 'Widget C', '120'],
        ['P004', 'Widget D', '150'],
    ]
    sales = [
        ['P001', '10'],
        ['P002', '5'],
        ['P003', '15'],
        ['P004', '2'],
    ]
    returns = [
        ['P001', '2'],
        ['P002', '5'],
        ['P003', '0'],
        ['P004', '5'],
    ]
    
    expected = [
        {'code': 'P002', 'reason': 'Net Sales is 0 or less'},
        {'code': 'P003', 'reason': 'High inventory (>=100) and low net sales (<20)'},
        {'code': 'P004', 'reason': 'Both conditions met'},
    ]

    create_test_csvs(inventory, sales, returns)
    run_report_script()
    if verify_report(expected):
        print("Test Case 1 PASSED")
        return True
    else:
        print("Test Case 1 FAILED")
        return False

if __name__ == "__main__":
    print("TEST_SUITE_READY")
    success = test_case_1()
    if success:
        exit(0)
    else:
        exit(1)
