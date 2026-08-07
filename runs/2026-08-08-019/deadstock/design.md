# Design Document: Deadstock Report Generation

## 1. Structure
This system calculates net sales for products listed in the inventory and identifies "deadstock" items based on a specific sales threshold.

### 1.1 File Configuration
- **Input Files (Read-Only)**:
    - `inventory.csv`: Master list of products.
    - `sales.csv`: History of sales transactions.
    - `returns.csv`: History of returned items.
- **Output File**:
    - `deadstock_report.txt`: The final report identifying deadstock products.

### 1.2 Data Flow
1. **Load Master List**: Read all product codes and names from `inventory.csv`.
2. **Aggregate Sales**: 
    - Filter `sales.csv` for records between `2026-05-01` and `2026-07-31`.
    - Sum the quantities per product code.
3. **Aggregate Returns**: 
    - Filter `returns.csv` for records between `2026-05-01` and `2026-07-31`.
    - Sum the quantities per product code.
4. **Calculate Net Sales**:
    - For each product in the master list: `Net Sales = Total Sales Quantity - Total Returns Quantity`.
5. **Filter Deadstock**:
    - Identify products where `Net Sales <= 0`.
6. **Generate Report**:
    - Format the identified products and their net sales into `deadstock_report.txt`.

### 1.3 Responsibility Division
- **Data Extraction Layer**: Responsible for reading CSVs and filtering by date range.
- **Calculation Layer**: Responsible for summing quantities and performing the subtraction.
- **Reporting Layer**: Responsible for formatting the final text output.

## 2. Quality Characteristics and Implementation

### 2.1 Handling of Missing Data
- **Missing Product Records**: If a product listed in `inventory.csv` does not appear in `sales.csv` or `returns.csv` for the specified period, the quantity for that specific file shall be treated as `0`.
- **Example**: If Product P004 is in inventory but has no sales and no returns, its net sales are calculated as `0 - 0 = 0`, and it is classified as deadstock.

### 2.2 Verifiability (Self-Test)
The implementation script must include a self-test phase.
- The script must print the number of processed items and the number of identified deadstock items.
- Success/Failure must be indicated by a specific ASCII marker: `[TEST_RESULT: OK]` or `[TEST_RESULT: NG]`.
- The script must not rely solely on the exit code; it must output these markers to stdout.

## 3. Design Rules

### 3.1 File Access Rules
- **Input files (`inventory.csv`, `returns.csv`, `sales.csv`) are read-only**. The implementer must not overwrite, edit, or delete these files.
- **No temporary files**: Do not create intermediate CSVs or temporary logs in the working directory. All calculations should be done in memory or via variables.
- **Output constraint**: Only create the file explicitly named in the specification: `deadstock_report.txt`.

### 3.2 Output Format (`deadstock_report.txt`)
The report must follow this structure:
- A header containing the string "死に筋商品".
- A list of products identified as deadstock.
- For each product, the report must include:
    - Product Code
    - Product Name
    - The calculated "正味販売数" (Net Sales) value.

Example Format:
```
死に筋商品 リスト
------------------
商品コード: P00X, 商品名: XXX, 正味販売数: -1
商品コード: P00Y, 商品名: YYY, 正味販売数: 0
```

### 3.3 General Coding Rules
- Use explicit date range filtering: `2026-05-01` to `2026-07-31`.
- Ensure all products in `inventory.csv` are iterated over, regardless of whether they have transaction history.
