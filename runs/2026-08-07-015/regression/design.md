# Design Document: Dead Stock Identification System

## 1. Structure

### 1.1 Data Flow
1. **Input Phase**: Read `inventory.csv`, `sales.csv`, and `returns.csv`.
2. **Aggregation Phase**: 
   - Calculate total quantity per product code from `sales.csv`.
   - Calculate total quantity per product code from `returns.csv`.
3. **Calculation Phase**: 
   - For each product code in `inventory.csv`, compute `Net Sales = Total Sales - Total Returns`.
4. **Classification Phase**: 
   - Evaluate each product against Dead Stock criteria.
5. **Output Phase**: Generate `dead_stock_report.txt` with identified products and reasons.

### 1.2 Responsibilities
- **Data Loader**: Responsible for reading CSV files and handling potential missing files or empty data.
- **Calculator**: Responsible for calculating Net Sales per product.
- **Classifier**: Responsible for applying business logic to determine if a product is "Dead Stock".
- **Reporter**: Responsible for formatting the output into the specified text file.

## 2. Quality Characteristics and Implementation Structure

### 2.1 Verifiability
To ensure the logic is correctly implemented and the script doesn't silently fail:
- **Internal Validation**: The implementation must track the number of products processed and the number of dead stock items found.
- **Self-Test Output**: If a test mode is implemented, it must print the number of test cases executed and the result using the following marker:
  `[TEST_RESULT: <executed_count>/<success_count>]`

### 2.2 Robustness
- Handle products that appear in `inventory.csv` but have no entries in `sales.csv` or `returns.csv` (treat as 0).
- Ensure calculations use numeric types to avoid string concatenation errors.

## 3. Design Rules

### 3.1 General Rules
- **Read-Only Inputs**: The input files (`inventory.csv`, `sales.csv`, `returns.csv`) must be treated as read-only. They must not be modified, overwritten, or deleted.
- **Minimal Artifacts**: Only the specified output file `dead_stock_report.txt` shall be created. No temporary files should be left in the working directory.

### 3.2 Dead Stock Logic Mapping
| Criterion | Condition | Logic |
| :--- | :--- | :--- |
| Condition A | Net Sales $\le$ 0 | `(Sum of Sales) - (Sum of Returns) <= 0` |
| Condition B | Overstock & Low Sales | `(Inventory >= 100) AND (Net Sales < 20)` |
| **Final Verdict** | **Dead Stock** | `Condition A OR Condition B` |

### 3.3 Output Layout (`dead_stock_report.txt`)
The report shall list all identified dead stock products in the following format:

```
--- Dead Stock Report ---
Product Code: [ProductCode]
Product Name: [ProductName]
Inventory: [Quantity]
Net Sales: [NetSales]
Reason: [Condition A / Condition B / Both]
-------------------------
```
*(Repeat for each dead stock product)*

**Specific strings to be used for reasons:**
- "Net Sales is 0 or less" (for Condition A)
- "High inventory (>=100) and low net sales (<20)" (for Condition B)
- "Both conditions met" (if both are true)
