ACHIEVED: The script analyze_deadstock.ps1 correctly implements the required logic to identify deadstock products based on the provided PURPOSE and SPEC.md.

REASON:
- The script correctly reads the three required CSV files (inventory, sales, returns).
- It calculates the net sales for each product using the formula: `Net Sales = Total Sales - Total Returns`.
- It applies the specific constraint (Net Sales <= 10) as defined in the acceptance criteria of SPEC.md.
- It outputs the results to report.txt, including the product name and the net sales figure as justification for being labeled as deadstock.
- No constraints from the original PURPOSE were weakened in SPEC.md; the operational definition of "deadstock" was concretized to "net sales <= 10" and the script adheres to this.

GAP:
- None. The implementation aligns with the specifications.
