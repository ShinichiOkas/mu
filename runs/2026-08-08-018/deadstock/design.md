# Design Document: Deadstock Identification System

## 1. Structure

### 1.1 File Configuration
- **Input Files (Read-Only)**:
    - `inventory.csv`: Master list of products (ProductCode, ProductName, StockCount).
    - `sales.csv`: Sales history (Date, ProductCode, Quantity).
    - `returns.csv`: Returns history (Date, ProductCode, Quantity).
- **Output File**:
    - `deadstock_report.txt`: Final report listing deadstock products and the calculation logic.

### 1.2 Data Flow
1. **Load Inventory**: Read `inventory.csv` to identify the set of target product codes.
2. **Aggregate Sales**: Scan `sales.csv` and sum the quantities for each product code.
3. **Aggregate Returns**: Scan `returns.csv` and sum the quantities for each product code.
4. **Calculate Net Sales**: For each product in the inventory:
   - `Net Sales = (Total Sales Quantity) - (Total Returns Quantity)`
5. **Identify Deadstock**: Filter products where `Net Sales <= 0`.
6. **Generate Report**: Write the criteria and the list of filtered products to `deadstock_report.txt`.

### 1.3 Responsibility Split
- **Data Access Layer**: Handles CSV parsing and reading.
- **Logic Layer**: Performs summation and the Net Sales calculation.
- **Reporting Layer**: Formats the output string and writes to the file.

## 2. Quality Attributes and Realization Structure

### 2.1 Verifiability
To ensure the implementation is correct and doesn't silently fail (exit 0 without doing work), the implementation script must include a self-test/log mechanism:
- **Execution Marker**: The script must print the number of products processed and the number of deadstock items found to the standard output.
- **Verification Pattern**: Use a marker like `[PROCESSED: X, DEADSTOCK: Y]` in the console output to verify the logic was actually executed.

### 2.2 Correctness
- **Edge Case Handling**: 
    - If a product exists in `inventory.csv` but has no entries in `sales.csv` or `returns.csv`, its sales/returns count shall be treated as 0.
    - Ensure negative values in returns are handled as additions or subtractions based on the CSV's numeric representation (assuming quantities are positive integers and the logic handles the subtraction).

## 3. Design Rules

### 3.1 Resource Constraints
- **Input files are read-only**: The script MUST NOT overwrite, edit, or delete `inventory.csv`, `returns.csv`, or `sales.csv`.
- **Clean Workspace**: Create only the file explicitly required by the specification (`deadstock_report.txt`). No temporary files should be left in the working directory.

### 3.2 Logic Specifications
- **Formula for Net Sales**: `純売上数 = (sales.csvの数量合計) - (returns.csvの数量合計)`
- **Condition for Deadstock**: `純売上数 <= 0`

### 3.3 Output Format (`deadstock_report.txt`)
The file must follow this structure:
1. **Criteria Section**: Must contain the exact phrase "純売上数 = 売上合計 - 返品合計 が0以下であること".
2. **Product List Section**: A list of products meeting the condition, formatted as:
   `[ProductCode], [ProductName], [Net Sales]` (Example: `P003, Widget A, -2`)
