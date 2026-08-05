# Design Document: Deadstock Report Generation

## 1. Structure

### 1.1 File Configuration
- **Input Files (Read-Only):**
  - `inventory.csv`: Product master (Product Code, Product Name, Stock Quantity).
  - `sales.csv`: Sales history (Date, Product Code, Quantity).
  - `returns.csv`: Returns history (Date, Product Code, Quantity).
- **Output File:**
  - `deadstock_report.txt`: A report containing identified deadstock products and the reasoning.

### 1.2 Data Flow and Responsibilities
1. **Data Loading & Normalization:**
   - Load `inventory.csv` to establish the base product list.
   - Load `sales.csv` and `returns.csv`. 
   - **Normalization:** Product codes must be treated as case-insensitive (e.g., `P008` and `p008` are the same).
2. **Aggregation (Net Sales Calculation):**
   - For each product code in the inventory:
     - Calculate `Total Sales` = sum of quantities in `sales.csv`.
     - Calculate `Total Returns` = sum of quantities in `returns.csv`.
     - Calculate `Net Sales` = `Total Sales` - `Total Returns`.
3. **Deadstock Identification Logic:**
   - A product is marked as "Deadstock" if either of the following conditions is true:
     - `Net Sales <= 0`
     - `(Inventory > 0) AND (Net Sales < 10)`
4. **Report Generation:**
   - Filter products that meet the deadstock criteria.
   - Generate the text report based on the specified format.

## 2. Quality Characteristics and Implementation Structure

### 2.1 Verification and Testability
To ensure the implementation is correct, the following verification markers must be used in self-tests (if implemented as a script):
- **Self-Test Output:** If a test script is run, it must print the number of tests executed and the results using a marker like `[TEST_RESULT: 5/5 PASSED]`.
- **Exit Codes:** The process must exit with code `0` only if the report is successfully generated and the data integrity is maintained.

### 2.2 Accuracy of Logic
- The "Net Sales" must account for negative values if returns exceed sales.
- Case sensitivity in product codes must be handled to avoid missing sales/returns (e.g., `p008` in `sales.csv` mapping to `P008` in `inventory.csv`).

## 3. Design Rules

### 3.1 Input/Output Rules
- **Read-Only Inputs:** `inventory.csv`, `sales.csv`, and `returns.csv` must NOT be modified, overwritten, or deleted.
- **Strict Output:** Only `deadstock_report.txt` shall be created. No temporary files (e.g., `.tmp`, `.bak`) should remain in the working directory.
- **Encoding:** The output file must be encoded in UTF-8.

### 3.2 Report Format
The `deadstock_report.txt` must follow this comma-separated format:
- **Columns:** `商品コード,商品名,在庫数,純売上数,判定理由`
- **Calculation Logic for Reason:**
  - If `Net Sales <= 0`: "純売上数が0以下のため"
  - If `(Inventory > 0) AND (Net Sales < 10)`: "純売上数が10個未満のため"
- **Example Line:** `P003,消しゴム,200,(-30),純売上数が10個未満のため` (Note: The specific example in SPEC.md uses "10個未満" for -30, implying that any value < 10, including negative, falls under this reason if not purely 0).
- **Refined Reason Logic (per SPEC):**
  - Since the SPEC example `P003,消しゴム,200,(-30), 純売上数が10個未満のため` suggests a specific string, the logic should be:
    - If `Net Sales < 10` (covers both `<=0` and `<10` cases), the reason is "純売上数が10個未満のため".
    - However, to strictly follow "Net Sales <= 0 OR (Inventory > 0 AND Net Sales < 10)", both are "Deadstock". The report reason should be descriptive of the threshold breached.
    - *Implementation Rule:* Use "純売上数が10個未満のため" for any `Net Sales < 10`.
