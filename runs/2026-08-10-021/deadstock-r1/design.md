# Design Document: Deadstock Report Generation

## 1. Structure

### 1.1 Data Flow
The system shall process data in the following sequence to identify deadstock products:
1. **Inventory Loading**: Read `inventory.csv` to establish the master list of product IDs and names.
2. **Sales Aggregation**: Read `sales.csv` and sum quantities grouped by product ID.
3. **Returns Aggregation**: Read `returns.csv` and sum quantities grouped by product ID.
4. **Net Sales Calculation**: For each product in the inventory, calculate the net sales using the formula defined below.
5. **Deadstock Filtering**: Filter products where net sales $\le 0$.
6. **Report Generation**: Write the filtered list to `deadstock_report.txt`.

### 1.2 Responsibilities
- **Data Access Layer**: Responsible for reading the three CSV files without modifying them.
- **Calculation Logic**: Responsible for case-insensitive ID matching and the Net Sales formula.
- **Reporting Layer**: Responsible for formatting the final text output.

## 2. Quality Characteristics and Verification Structure

### 2.1 Verification Strategy
To ensure the implementation is correct, any verification script must not rely solely on the process exit code.
- **Verification Marker**: Future verification scripts must print a specific ASCII marker upon successful completion of all checks.
- **Marker String**: `[VERIFICATION_SUCCESS]`
- **Requirement**: The script must print the number of tests executed and the results (e.g., `Tests: 3, Passed: 3`).

### 2.2 Robustness
- **Case Insensitivity**: All product ID comparisons must be performed case-insensitively (e.g., 'P001' == 'p001').
- **Empty Sets**: If no deadstock products are found, the report must explicitly state that no deadstock items were identified.

## 3. Design Rules

### 3.1 Constraints
- **Read-Only Inputs**: The input files (`inventory.csv`, `sales.csv`, `returns.csv`) must be treated as **read-only**. They shall not be modified, overwritten, or deleted.
- **Artifact Minimization**: Only the specified output file (`deadstock_report.txt`) shall be created. No temporary files or logs shall be left in the working directory.

### 3.2 Net Sales Formula
The Net Sales for a specific product is calculated as:
`Net Sales = (Sum of quantities in sales.csv for Product ID) - (Sum of quantities in returns.csv for Product ID)`

### 3.3 Output Format (`deadstock_report.txt`)
The report shall follow this layout:

**Case A: Deadstock products found**
```
Deadstock Product Report
-----------------------
Product Code: [Product Code]
Product Name: [Product Name]
Net Sales: [Calculated Value]
-----------------------
(Repeat for each deadstock product)
```

**Case B: No deadstock products found**
```
No deadstock products were identified.
```
