"""Minimal reproduction of the round-trip bug in concatenate/split"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

from rest_framework_api_key.crypto import concatenate, split

# Minimal failing example found by Hypothesis
left = "."
right = "0"

concatenated = concatenate(left, right)
result_left, result_right = split(concatenated)

print(f"Input:    left='{left}', right='{right}'")
print(f"Concatenated: '{concatenated}'")
print(f"Output:   left='{result_left}', right='{result_right}'")
print()
print(f"Expected: ({repr(left)}, {repr(right)})")
print(f"Got:      ({repr(result_left)}, {repr(result_right)})")
print()

if (result_left, result_right) != (left, right):
    print("BUG: Round-trip property violated!")
    print(f"The split function fails to correctly inverse concatenate when left='{left}'")
else:
    print("No bug found")