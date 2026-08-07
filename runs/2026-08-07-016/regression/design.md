# Architectural Design: Dead Stock Identification System

## 1. Structure

### 1.1 File Structure and Responsibilities
The system will be implemented as a single-purpose script.

- **`dead_stock_analyzer.ps1`** (Implementation target):
    - **Data Loading**: Reads `inventory.csv`, `sales.csv`, and `returns.csv`.
    - **Aggregation**: Calculates the 'Net Sales Quantity' (正味販売数量) for each product.
    - **Classification**: Applies dead stock criteria to identify target products.
    - **Reporting**: Generates `dead_stock_report.txt` with the required evidence.

### 1.2 Data Flow
1. **Input Phase**: 
   - Load `inventory.csv` into a product master list.
   - Load `sales.csv` and `returns.csv` into transaction lists.
2. **Calculation Phase**:
   - For each product in `inventory.csv`:
     - Sum quantities from `sales.csv` $\rightarrow$ `TotalSales`
     - Sum quantities from `returns.csv` $\rightarrow$ `TotalReturns`
     - Calculate: `NetSalesQuantity` = `TotalSales` - `TotalReturns`
3. **Classification Phase**:
   - Mark as "Dead Stock" if:
     - `NetSalesQuantity` $\le 0$
     - OR (`NetSalesQuantity` $> 0$ AND `InventoryCount` $\ge 100$)
4. **Output Phase**:
   - Filter only "Dead Stock" products.
   - Write results to `dead_stock_report.txt`.

### 1.3 Output Format (`dead_stock_report.txt`)
The report shall list each dead stock product in the following format:
```text
Product Code: [Code]
Reason: [Reason Description] (Net Sales Quantity: [Value], Inventory: [Value])
-------------------------------------------
```
Example:
`Product Code: P003`
`Reason: Low sales volume (Net Sales Quantity: -2, Inventory: 50)`

## 2. Quality Attributes and Implementation Structure

### 2.1 Verifiability (Self-Test)
To ensure the script actually processed data and didn't simply exit with code 0, the implementation must include a self-test mode or verbose output that prints the number of processed records and the number of identified dead stock items.

- **Execution Marker**: The script must output a summary marker upon completion:
  `RESULT: [Processed: X, Identified: Y]`
- This prevents "silent failures" where the script runs without error but produces an empty report.

### 2.2 Robustness
- **Missing Data**: If a product exists in `inventory.csv` but has no entries in `sales.csv` or `returns.csv`, the sum shall be treated as 0.

## 3. Design Rules

### 3.1 File Handling
- **Input files are read-only**: `inventory.csv`, `sales.csv`, and `returns.csv` must NOT be modified, overwritten, or deleted.
- **Strict Output**: Only the file `dead_stock_report.txt` shall be created. No temporary files should be left in the working directory.

### 3.2 Logic Constants
- **Dead Stock Threshold (Inventory)**: $\ge 100$
- **Dead Stock Threshold (Net Sales)**: $\le 0$

### 3.3 Naming and Terms
- The term **"正味販売数量"** must be used in the internal logic and documentation to align with the SPEC.
