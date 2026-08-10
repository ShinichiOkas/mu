# Design Document: Deadstock Report Generator

## 1. Structure

### File Configuration
- **Input Files**:
    - `inventory.csv`: Master list of current stock.
    - `sales.csv`: Transaction logs of items sold.
    - `returns.csv`: Transaction logs of items returned.
- **Output File**:
    - `deadstock_report.txt`: A text report listing items identified as deadstock.

### Data Flow
1. **Ingestion**: Load all three CSV files. Product codes must be treated case-insensitively (e.g., `P008` and `p008` are the same).
2. **Aggregation**:
    - Calculate total sales quantity per product code from `sales.csv`.
    - Calculate total return quantity per product code from `returns.csv`.
3. **Calculation**: Compute **Net Sales Volume** for each product.
4. **Filtering**: Apply Deadstock logic to the inventory list.
5. **Reporting**: Format the filtered list into the final text report.

### Responsibility Division
- **Data Provider**: CSV files (Read-only).
- **Processing Logic**: 
    - `Net Sales Volume = Σ(sales.数量) - Σ(returns.数量)`
    - `Is Deadstock = (inventory.在庫数 > 0) AND (Net Sales Volume <= 0)`
- **Formatter**: Transforms the list of deadstock items into the specified report layout.

## 2. Quality Characteristics and Realization Structure

### Verifiability
To ensure the implementation is correct and not just exiting with code 0, the implementation must include a self-test mechanism that outputs a specific ASCII marker.

- **Self-Test Requirement**: The script must execute a set of internal test cases (e.g., mock data for sales, returns, and inventory) and print the result.
- **ASCII Marker**: The script must print `[TEST_RESULT: OK]` if all internal tests pass, or `[TEST_RESULT: FAIL]` otherwise.

### Robustness
- **Case Sensitivity**: Product codes must be normalized to uppercase during all mapping and aggregation processes.
- **Missing Data**: If a product in `inventory.csv` has no entries in `sales.csv` or `returns.csv`, its sales and return volumes are treated as 0.

## 3. Design Rules

### File Access Rules
- **Input files are read-only**. The program MUST NOT overwrite, edit, or delete `inventory.csv`, `returns.csv`, or `sales.csv`.
- **Output isolation**: Only `deadstock_report.txt` may be created. No temporary files should be left in the working directory.

### Logic Rules
- **Net Sales Volume Calculation**:
    - `sales.csv` column `数量` $\rightarrow$ Summed as Total Sales.
    - `returns.csv` column `数量` $\rightarrow$ Summed as Total Returns.
    - `Net Sales Volume = Total Sales - Total Returns`.
- **Deadstock Identification**:
    - An item is deadstock if `Inventory Count > 0` AND `Net Sales Volume <= 0`.

### Report Layout (`deadstock_report.txt`)
The report must follow this exact format:
```
--- Deadstock Report ---
[Product Code] [Product Name] (Stock: [Count])
...
------------------------
Total Deadstock Items: [Count]
```
Example:
```
--- Deadstock Report ---
P007 ホッチキス (Stock: 60)
P010 蛍光ペン (Stock: 75)
------------------------
Total Deadstock Items: 2
```

### Implementation Constraints
- **Language**: Any language that can run in the provided environment.
- **Marker**: Ensure the `[TEST_RESULT: OK]` marker is printed to stdout during the test phase.
