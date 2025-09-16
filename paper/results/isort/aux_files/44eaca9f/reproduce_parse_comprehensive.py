import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.comments as comments

test_cases = [
    "#0",           # Comment with no space after #
    "#test",        # Comment with no space after #
    "# test",       # Comment with space after #
    "#",            # Just the hash character
    "##",           # Double hash
    "import os#x",  # Import with comment no space
    "import os # x", # Import with comment and space
]

for line in test_cases:
    import_part, comment_part = comments.parse(line)
    print(f"Input: '{line}'")
    print(f"  Parsed: import='{import_part}', comment='{comment_part}'")
    
    # Try to reconstruct
    if comment_part:
        # Common reconstruction pattern
        reconstructed = f"{import_part}# {comment_part}"
        matches = reconstructed == line
        print(f"  Reconstructed: '{reconstructed}'")
        print(f"  Matches original? {matches}")
    elif import_part == line:
        print(f"  No comment, import_part matches original: OK")
    else:
        print(f"  ERROR: No comment but import_part != original")
    print()