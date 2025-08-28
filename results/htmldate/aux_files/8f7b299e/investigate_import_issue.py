"""Test what happens when functions are completely missing from imports."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import htmldate.meta

# Save original function
original_compare = htmldate.meta.compare_reference

print("Testing scenario where compare_reference is completely missing...")

# Replace with a non-cached function
def fake_compare_reference(*args, **kwargs):
    return 0

# Replace the import in meta.py
htmldate.meta.compare_reference = fake_compare_reference

# Now reset_caches should fail with AttributeError
try:
    htmldate.meta.reset_caches()
    print("BUG FOUND: reset_caches() did not raise AttributeError when compare_reference lacks cache_clear!")
    print("This is a real bug - the function should check if cache_clear exists before calling it.")
except AttributeError as e:
    print(f"Good: AttributeError raised: {e}")

# Restore
htmldate.meta.compare_reference = original_compare

print("\nLet's check the actual source to understand the issue...")
with open('/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages/htmldate/meta.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[23:33], 24):
        print(f"{i}: {line.rstrip()}")