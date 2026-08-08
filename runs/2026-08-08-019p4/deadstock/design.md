# Design Document: Deadstock Identification System

## 1. Structure

### 1.1 File Organization
- **Input Files (Read-Only)**:
  - `inventory.csv`: Master list of products (`商品コード`, `商品名`, `在庫数`).
  - `sales.csv`: Sales transaction history (`日付`, `商品コード`, `数量`).
  - `returns.csv`: Returns transaction history (`日付`, `商品コード`, `数量`).
- **Output File**:
  - `deadstock_report.txt`: Final report containing the list of deadstock products.

### 1.2 Data Flow and Responsibilities
The system shall process data in the following stages:
1. **Loading**: Load `inventory.csv` to establish the universe of target products.
2. **Aggregation**:
   - Sum the `数量` (Quantity) from `sales.csv` grouped by `商品コード`.
   - Sum the `数量` (Quantity) from `returns.csv` grouped by `商品コード`.
   - **Case Sensitivity**: Product codes must be treated case-insensitively (e.g., `P008` and `p008` are the same product).
3. **Calculation**:
   - For each product in the inventory list, calculate the **Net Sales**.
   - **Formula**: `Net Sales = (Total Sales Quantity) - (Total Returns Quantity)`
   - **Missing Data Handling**: If a product code from `inventory.csv` is missing in `sales.csv` or `returns.csv`, the respective quantity shall default to `0`.
4. **Filtering**:
   - A product is identified as **Deadstock** if `Net Sales <= 0`.
5. **Reporting**: Generate `deadstock_report.txt` based on the filtered list.

## 2. Quality Characteristics and Realization Structure

### 2.1 Validation and Verifiability
To ensure the implementation is correct and not just returning a success exit code, the following verification mechanism is defined:
- **Self-Test Marker**: The implementation script must output a verification summary to the console upon completion.
- **Format**: `[TEST] Executed: {N} items | Identified: {M} deadstock | Result: {PASS/FAIL}`
- This allows the operator to verify that the script actually processed the data and found the expected number of items.

### 2.2 Robustness
- **Empty Files**: The system must handle cases where `sales.csv` or `returns.csv` are empty (treating all quantities as 0).
- **Data Integrity**: Only products present in `inventory.csv` are reported, regardless of whether they appear in sales/returns files.

## 3. Design Rules

### 3.1 Input/Output Constraints
- **Read-Only Inputs**: `inventory.csv`, `sales.csv`, and `returns.csv` MUST NOT be modified, moved, or deleted.
- **Minimal Output**: Only the file explicitly specified (`deadstock_report.txt`) shall be created. No temporary files or logs should be left in the working directory.

### 3.2 Report Format (`deadstock_report.txt`)
The report must strictly follow this structure:
- **Header**: `死に筋商品リスト`
- **Criteria Section**: A brief explanation stating that deadstock is defined as products with a Net Sales (純販売数) of 0 or less.
- **Product List**: For each deadstock item, list:
  - `[商品コード] 商品名 (純販売数: {Value})`
- **Example**:
  ```
  死に筋商品リスト
  判定基準: 純販売数(売上合計 - 返品合計)が0以下であること。

  P007 ホッチキス (純販売数: 0)
  P003 消しゴム (純販売数: 10) -> (Example: if returns were higher)
  ```
  *(Note: The actual content depends on the calculated data)*

### 3.3 Implementation Rules
- Use case-insensitive matching for product codes.
- Ensure the output is encoded in a format compatible with Windows PowerShell (e.g., UTF-8 with BOM or Shift-JIS as appropriate for the environment).
