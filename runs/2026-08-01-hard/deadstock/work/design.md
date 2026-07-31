# Design Document: Deadstock Calculation Script

## 1. Structure

### 1.1. File Configuration
- **Input Files**: 
    - `inventory.csv`: Product master (Product ID, Product Name)
    - `sales.csv`: Sales history (Date, Product ID, Quantity)
    - `returns.csv`: Return history (Date, Product ID, Quantity)
- **Output File**: 
    - `deadstock_report.csv`: List of deadstock products.

### 1.2. Data Flow & Responsibility
The script shall be decomposed into the following logical steps:

1.  **Data Loading**:
    - Read `inventory.csv`, `sales.csv`, and `returns.csv`.
2.  **Time Filtering**:
    - Identify the "current date" (Reference Date) as the maximum date found across `sales.csv` and `returns.csv`.
    - Filter records where `Date` is within the range `[Reference Date - 90 days, Reference Date]`.
3.  **Aggregation**:
    - Group `sales.csv` (filtered) by `Product ID` $\rightarrow$ Sum of Quantities.
    - Group `returns.csv` (filtered) by `Product ID` $\rightarrow$ Sum of Quantities.
4.  **Joining & Calculation**:
    - Perform a Left Join: `inventory.csv` $\leftarrow$ `Aggregated Sales` $\leftarrow$ `Aggregated Returns`.
    - Calculate **Net Sales**: `Net Sales (Sales - Returns)`.
    - Handle missing values (nulls) as 0.
5.  **Deadstock Identification**:
    - Filter products where `Net Sales == 0`.
6.  **Report Generation**:
    - Extract `Product ID`, `Product Name`, and `Net Sales`.
    - Write to `deadstock_report.csv`.

### 1.3. Output Schema (`deadstock_report.csv`)
| Column | Type | Description |
| :--- | :--- | :--- |
| Product ID | String | Unique identifier of the product |
| Product Name | String | Name of the product from inventory.csv |
| Net Sales | Integer | Calculation: Sales - Returns (Must be 0) |

---

## 2. Quality Characteristics & Realization

### 2.1. Verification Mechanism
To ensure the script is not a "silent failure" (returning exit 0 without doing anything), the implementation must include a self-test or log output.

- **Execution Marker**: The script must print a summary to the console upon completion.
- **Marker Format**: 
    `[SUMMARY] Processed: {N} products, Deadstock identified: {M} products.`
- **Verification Logic**: 
    - The QA process will verify that the `deadstock_report.csv` is not only present but contains the exact header `Net Sales`.

---

## 3. Design Rules

### 3.1. File Handling
- **Read-Only Inputs**: `inventory.csv`, `sales.csv`, and `returns.csv` MUST NOT be modified, overwritten, or deleted.
- **Strict Output**: Only `deadstock_report.csv` shall be created as a result. No temporary files (e.g., `temp.csv`, `joined.csv`) should be left in the working directory.

### 3.2. Logic Constraints
- **Date Range**: The 90-day window is inclusive of the reference date.
- **Missing Data**: If a product exists in `inventory.csv` but has no entries in `sales.csv` or `returns.csv` for the 90-day period, its `Net Sales` is considered 0 (and thus it is deadstock).
- **Header Accuracy**: The output CSV header must exactly match the requirement: `Product ID, Product Name, Net Sales`.

### 3.3. ASCII Markers
- **Console Output**: `[SUMMARY]`
