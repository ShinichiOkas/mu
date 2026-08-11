# Design Document: Unprofitable Products Identification

## 1. Structure

### 1.1 Data Flow
`sales.csv` (Input) $\rightarrow$ `Processing Script` $\rightarrow$ `unprofitable_products.txt` (Output)

### 1.2 Component Responsibilities
- **Input Handler**: Reads `sales.csv`. Must treat the file as read-only.
- **Calculation Engine**: 
    - Calculates the Gross Profit Margin for each product.
    - Formula: `(Price - Cost) / Price`
- **Filter**: 
    - Identifies products where the Gross Profit Margin is less than the threshold.
    - Threshold: `0.15` (15%)
- **Output Handler**: Writes the list of products meeting the criteria to `unprofitable_products.txt`.

### 1.3 Data Schema
- **Input (`sales.csv`)**: Expected columns include Product Name, Price, and Cost.
- **Output (`unprofitable_products.txt`)**: A text file containing the names of products with a margin < 0.15.

## 2. Quality Characteristics and Realization Structure

### 2.1 Verifiability (Self-Test)
To ensure the script is not exiting silently without executing logic, the implementation must include a verification mechanism:
- The script shall print the number of records processed and the number of unprofitable products found.
- **ASCII Marker**: The script must output `[TEST_RESULT: SUCCESS]` upon successful completion of the data flow.
- **Exit Code**: The script must return exit code 0 only if the data flow was completed and the output file was written.

## 3. Design Rules

### 3.1 File Handling Rules
- **Read-Only Input**: `sales.csv` is a protected input file. It must NOT be overwritten, edited, or deleted.
- **Strict Output**: Only `unprofitable_products.txt` shall be created as a final artifact. No temporary files should be left in the working directory.
- **Overwrite Policy**: The output file `unprofitable_products.txt` should be overwritten on each execution to ensure data freshness.

### 3.2 Calculation Rules
- **Precision**: Use floating-point arithmetic for the margin calculation.
- **Zero Division**: If `Price` is 0, the product should be treated as unprofitable or handled to avoid runtime crashes.

### 3.3 Mandatory Markers
- The implementation must produce the following marker in the console output upon completion:
  `[TEST_RESULT: SUCCESS]`
