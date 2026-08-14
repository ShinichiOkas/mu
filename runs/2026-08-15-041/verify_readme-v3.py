import os
import ast
import json
import re

def get_py_files_info():
    """
    Scans the current directory for .py files and extracts their filenames 
    and top-level docstrings (roles).
    """
    info = {}
    # Filter only .py files in the current directory
    py_files = [f for f in os.listdir('.') if f.endswith('.py') and f != 'verify_readme.py']
    
    for filename in py_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                # The role is the module-level docstring
                doc = ast.get_docstring(tree)
                info[filename] = doc.strip() if doc else ""
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            info[filename] = ""
    return info

def analyze_readme():
    """
    Parses README.md to find mentions of .py files and their roles.
    """
    if not os.path.exists('README.md'):
        return None
    
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    return content

def main():
    py_info = get_py_files_info()
    readme_content = analyze_readme()
    
    if readme_content is None:
        print("README.md not found.")
        return

    mismatches = []
    covered_files = set()
    
    # 1. Check for mismatches (Fact-checking README against implementation)
    # We look for file names in the README and check if their roles match.
    for filename, role in py_info.items():
        # Check if filename is mentioned
        if filename in readme_content:
            covered_files.add(filename)
            # If a role is specified in the py file, it should be in the README.
            # This is a simple check: if the exact role string is not in README, 
            # we consider it a potential mismatch IF it's meant to be described.
            # The spec says: "descriptions in README.md... contradiction with actual implementation"
            if role and role not in readme_content:
                mismatches.append(f"File {filename}: Role '{role}' not found in README.md")
        else:
            # Not mentioned at all (will be handled by 'All files covered')
            pass

    # Also check if there are file names in README that don't exist in implementation
    # We look for patterns like 'something.py'
    mentioned_py_files = re.findall(r'(\w+\.py)', readme_content)
    for mentioned in mentioned_py_files:
        if mentioned not in py_info:
            mismatches.append(f"README mentions {mentioned}, but it does not exist in implementation.")

    # Check total number of files mentioned vs actual
    # This is tricky because "total number" might be written as "There are 5 files".
    # We'll look for digits followed by "files" or similar.
    count_match = re.search(r'(\d+)\s+files?', readme_content)
    if count_match:
        claimed_count = int(count_match.group(1))
        actual_count = len(py_info)
        if claimed_count != actual_count:
            mismatches.append(f"README claims {claimed_count} files, but actual count is {actual_count}.")

    # 2. Check if all files are covered
    all_covered = set(py_info.keys()) == covered_files

    # Output results
    if not mismatches:
        print("No mismatches found")
    else:
        for m in mismatches:
            print(f"Mismatch: {m}")

    if all_covered:
        print("All files covered")
    else:
        missing = set(py_info.keys()) - covered_files
        print(f"Not all files covered. Missing: {', '.join(missing)}")

    # 3. Write to measure.json
    measure = {
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "all_covered": all_covered,
        "missing_files": list(set(py_info.keys()) - covered_files),
        "actual_file_count": len(py_info)
    }
    with open('measure.json', 'w', encoding='utf-8') as f:
        json.dump(measure, f, indent=4)

if __name__ == "__main__":
    main()
