# Design Document: Dead Stock Analysis System

## 1. Business Logic

### Net Sales Calculation
- **Formula**: `Net Sales = Total Quantity in sales.csv - Total Quantity in returns.csv`
- **Scope**: Aggregated per Product Code.

### Dead Stock Criteria
A product is classified as "Dead Stock" if it meets either of the following conditions:
1. **Net Sales $\le$ 0**
2. **(Net Sales / Inventory Quantity) < 0.1** (where Inventory Quantity is obtained from `inventory.csv`)

## 2. Structure

### File Configuration
- `analyze_dead_stock.ps1`: Main implementation script.
- `verify_dead_stock.ps1`: Verification script to ensure correctness.
- `dead_stock_report.txt`: Final report output.

### Data Flow
1. **Load Data**: Read `inventory.csv`, `sales.csv`, and `returns.csv`.
2. **Aggregate**: Sum quantities by Product Code for sales and returns.
3. **Calculate**: Determine Net Sales for each product.
4. **Evaluate**: Compare Net Sales and Inventory against Dead Stock criteria.
5. **Report**: Generate `dead_stock_report.txt` containing the list of Dead Stock products and their evidence (Net Sales, Inventory).

### Responsibilities
- `analyze_dead_stock.ps1`: Data processing, logic application, and report generation.
- `verify_dead_stock.ps1`: Validation of the report's existence and content.

## 3. Quality Characteristics and Verification Structure

### Verification Method
The verification script must not rely solely on the exit code. It must perform explicit checks and output results using a specific ASCII marker to indicate successful validation.

- **Verification Steps**:
    1. Check if `dead_stock_report.txt` exists.
    2. Check if `dead_stock_report.txt` contains the string "純売上数".
- **Success Marker**: Upon successful completion of all checks, the script must print `[VERIFICATION_PASSED]`.

## 4. Design Rules

### General Constraints
- **Read-Only Inputs**: Input files (`inventory.csv`, `sales.csv`, `returns.csv`) must be read-only. No overwriting, editing, or deleting.
- **Output Limitation**: Only the files specified in the specifications (`dead_stock_report.txt`) should be created as final artifacts. Do not leave temporary files in the working directory.
- **Encoding**: Use UTF-8 for all text files to ensure consistency.

### ASCII Markers
- Verification Success: `[VERIFICATION_PASSED]`
