# Design Document: Dead Stock Report Generator

## 1. Structure

### File Configuration
- **Input Files**:
  - `inventory.csv` (Columns: ProductCode, ProductName, StockQuantity)
  - `sales.csv` (Columns: Date, ProductCode, Quantity)
  - `returns.csv` (Columns: Date, ProductCode, Quantity)
- **Output File**:
  - `dead_stock_report.txt` (Text format report)

### Data Flow
1. **Load Inventory**: Read `inventory.csv` to establish the list of target products (ProductCode $\rightarrow$ ProductName).
2. **Aggregate Sales**: Read `sales.csv` and calculate the total quantity sold per `ProductCode`.
3. **Aggregate Returns**: Read `returns.csv` and calculate the total quantity returned per `ProductCode`.
4. **Calculate Actual Sales**: For each product in the inventory, apply the formula:
   `Actual Sales = Sum(sales.csv) - Sum(returns.csv)`
5. **Filter Dead Stock**: Identify products where `Actual Sales <= 0`.
6. **Generate Report**: Write the identified products and their calculation details to `dead_stock_report.txt`.

### Responsibility Division
- **Data Access Layer**: Reads CSV files and returns structured data (e.g., maps/dictionaries).
- **Logic Layer**: Performs aggregations, calculates Actual Sales, and filters based on the Dead Stock condition.
- **Output Layer**: Formats the results into the specified text report.

## 2. Quality Characteristics and Implementation Structure

### Verifiability
To ensure the implementation is not a "silent failure" (exit 0 without doing anything), the implementation must include a self-test/verification mechanism.
- **Verification Marker**: The final script must output a specific ASCII marker to the console upon successful completion of its logic.
- **Marker String**: `[VERIFICATION]: Processed X products, found Y dead stocks.` (where X and Y are actual numbers).

## 3. Design Rules

- **Input Immutability**: Input files (`inventory.csv`, `sales.csv`, `returns.csv`) are **read-only**. The implementation must not modify, overwrite, or delete them.
- **Output Isolation**: Create only the file explicitly required by the specification (`dead_stock_report.txt`). Do not leave temporary files or logs in the working directory.
- **Formula Adherence**: The calculation must strictly follow: `Actual Sales = Sum(sales.csv) - Sum(returns.csv)`.
- **Filtering Condition**: A product is considered "Dead Stock" if and only if:
  1. It exists in `inventory.csv`.
  2. Its `Actual Sales` is $\le 0$.
- **Report Format**: For each dead stock item, the report must include:
  - The Product Name.
  - The calculation basis (e.g., "Sales Total X - Returns Total Y = Actual Sales Z").
