# Schema Analysis: Deadstock Identification

This document defines the data schemas and constraints for the inventory, sales, and returns files based on `SPEC.md` and the provided CSV data.

## 1. Data Schemas

### 1.1 inventory.csv
**Role**: Master list of products.
| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| 商品コード | String | Unique product identifier | Primary Key |
| 商品名 | String | Name of the product | Non-empty |
| 在庫数 | Integer | Current stock level | $\ge 0$ |

### 1.2 sales.csv
**Role**: Transactional record of sales.
| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| 日付 | Date | Date of sale | Format: `YYYY-MM-DD` |
| 商品コード | String | Product identifier | Foreign Key to `inventory.csv` |
| 数量 | Integer | Quantity sold | $> 0$ |

### 1.3 returns.csv
**Role**: Transactional record of returns.
| Column | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| 日付 | Date | Date of return | Format: `YYYY-MM-DD` |
| 商品コード | String | Product identifier | Foreign Key to `inventory.csv` |
| 数量 | Integer | Quantity returned | $> 0$ |

## 2. Date Format and Filter Constraints

### 2.1 Date Format
- All date fields in `sales.csv` and `returns.csv` use the ISO 8601 extended format: **`YYYY-MM-DD`** (e.g., `2026-05-02`).

### 2.2 90-Day Filter Logic
- **Reference Date**: The "current date" for the 90-day calculation should be determined by the latest date present across both `sales.csv` and `returns.csv` (or the system date if specified, but for reproducibility in this context, the max date in the dataset is the standard baseline).
- **Filter Range**: $\text{Reference Date} - 90 \text{ days} \le \text{Transaction Date} \le \text{Reference Date}$.
- Only records falling within this window are counted towards the Net Sales calculation.

## 3. Business Logic Constraints
- **Case Sensitivity**: Product IDs (商品コード) may appear in different cases (e.g., `P008` and `p008`). These must be treated as the **same identifier** (case-insensitive matching).
- **Net Sales Calculation**:
  $\text{Net Sales (Product X)} = \sum(\text{sales.csv quantities for X}) - \sum(\text{returns.csv quantities for X})$
- **Deadstock Criteria**: $\text{Net Sales} = 0$ within the 90-day window.
