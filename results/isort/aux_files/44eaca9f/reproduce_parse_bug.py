import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.comments as comments

# Test case 1: Comment with no space after #
line1 = "#0"
import_part, comment_part = comments.parse(line1)
print(f"Input: '{line1}'")
print(f"Parsed: import_part='{import_part}', comment_part='{comment_part}'")
if comment_part:
    reconstructed = f"{import_part}# {comment_part}"
    print(f"Reconstructed: '{reconstructed}'")
    print(f"Matches original? {reconstructed == line1}")