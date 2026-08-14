import os
import json
import re

def get_impl_files():
    """
    Identify implementation files based on the project structure.
    Implementation files are .py files in the 'mu/' directory.
    """
    impl_files = []
    # Note: The script runs in a task directory where 'mu' might not be present.
    # But according to project structure, 'mu' is at the root of the clone.
    # The current directory is .mu-work\implementer\task-1.
    # The actual 'mu' directory is at ../../../mu.
    # However, the requirement says "absolute paths are forbidden".
    # I should check if 'mu' exists relative to the script.
    
    # To make it robust for different execution environments:
    # Check if 'mu' exists here, or in parents.
    search_paths = ['.', '..', '../..', '../../../']
    mu_dir = None
    for p in search_paths:
        candidate = os.path.join(p, 'mu')
        if os.path.exists(candidate) and os.path.isdir(candidate):
            mu_dir = candidate
            break
    
    if mu_dir:
        try:
            for f in os.listdir(mu_dir):
                if f.endswith('.py'):
                    impl_files.append(f) # Just the filename
        except OSError:
            pass
    return sorted(impl_files)

def verify():
    # 1. Get actual implementation files (filenames only)
    impl_files = get_impl_files()
    
    # 2. Read README.md
    # README.md is also likely at the root ../../../README.md
    readme_path = 'README.md'
    search_paths = ['.', '..', '../..', '../../../']
    for p in search_paths:
        candidate = os.path.join(p, 'README.md')
        if os.path.exists(candidate):
            readme_path = candidate
            break

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_text = f.read()
    except FileNotFoundError:
        readme_text = ""

    # 3. Count Factual Errors (factual_errors)
    # Definition: README mentions a file, role, or count that contradicts reality.
    factual_errors = 0
    
    # Extract all mentioned .py files in backticks
    mentioned_files = re.findall(r'`([^`]+\.py)`', readme_text)
    unique_mentioned = set(mentioned_files)
    
    for mf in unique_mentioned:
        if mf == 'verify_readme.py':
            continue
        
        # Extract filename from the mention (e.g., 'mu/l0.py' -> 'l0.py')
        mf_basename = os.path.basename(mf)
        
        # If the filename is not in the actual implementation, it's a factual error
        if mf_basename not in impl_files:
            factual_errors += 1

    # 4. Count Unmentioned Items (unmentioned_counts)
    # Definition: Implementation files not mentioned in README.md.
    unmentioned_counts = 0
    for ifile in impl_files:
        # If the filename is not mentioned anywhere in README, it's unmentioned
        if ifile not in readme_text:
            unmentioned_counts += 1

    # Result
    result = {
        "factual_errors": factual_errors,
        "unmentioned_counts": unmentioned_counts
    }
    
    # write measure.json in the current working directory
    with open('measure.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        
    # Print for verification command
    print(json.dumps(result))

if __name__ == "__main__":
    verify()
