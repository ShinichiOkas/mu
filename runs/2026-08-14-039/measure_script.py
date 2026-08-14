import os
import re
import json
import ast

def extract_docstring(file_path):
    """Extract the module-level docstring from a python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
            return ast.get_docstring(tree)
    except Exception:
        return None

def parse_expected_roles(readme_path):
    """Parse the README.md for the expected roles table."""
    roles = []
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find the roles table: looking for the table starting with | role |
            # The header is | role | 居場所 | 意味（職掌） | 見るもの | 生むもの | 権限 |
            # We find the start of this table and capture all subsequent rows starting with |
            table_start_pattern = re.compile(r'\| role \| 居場所 \|')
            match = table_start_pattern.search(content)
            if match:
                # Extract everything from the start of the header to the end of the table
                table_text = content[match.start():]
                lines = table_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line.startswith('|'):
                        break
                    # Split by | and remove empty elements from the ends
                    cols = [c.strip() for c in line.split('|') if c.strip()]
                    if not cols:
                        continue
                    # Skip header and separator rows (like |---|---|)
                    role_name = cols[0].replace('**', '').strip()
                    if role_name.lower() == 'role' or all(c == '-' for c in role_name):
                        continue
                    roles.append(role_name)
    except Exception as e:
        print(f"Error parsing README: {e}")
    return roles

def main():
    readme_path = 'README.md'
    output_path = 'measure.json'
    
    # 1. Get expected roles from README
    expected_roles = parse_expected_roles(readme_path)
    
    # 2. Scan .py files for docstrings
    results = {}
    # Scanning the current directory for .py files
    # We exclude the script itself to avoid noise
    for filename in os.listdir('.'):
        if filename.endswith('.py') and filename != 'measure_script.py':
            docstring = extract_docstring(filename)
            if docstring:
                # Check if any expected role is mentioned in the docstring
                found_roles = [role for role in expected_roles if role in docstring]
                results[filename] = {
                    "docstring": docstring,
                    "found_roles": found_roles
                }
            else:
                results[filename] = {
                    "docstring": None,
                    "found_roles": []
                }

    # 3. Comparison summary
    all_found_roles = set()
    for data in results.values():
        all_found_roles.update(data["found_roles"])
    
    missing_roles = [role for role in expected_roles if role not in all_found_roles]
    
    final_output = {
        "expected_roles": expected_roles,
        "file_analysis": results,
        "missing_roles": missing_roles
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully wrote results to {output_path}")

if __name__ == "__main__":
    main()
