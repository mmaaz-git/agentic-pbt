#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
from troposphere.validators.awslambda import validate_memory_size, validate_variables_name

# Bug 1: Memory size validation with negative numbers
print("=== Bug 1: Memory size validation ===")
try:
    validate_memory_size(-1)
except ValueError as e:
    print(f"Error for -1: {e}")
    print(f"Error type: {type(e).__name__}")

try:
    validate_memory_size(0)
except ValueError as e:
    print(f"Error for 0: {e}")

# Bug 2: Environment variable name validation  
print("\n=== Bug 2: Environment variable validation ===")

# The pattern from the code
pattern = r"[a-zA-Z][a-zA-Z0-9_]+"
test_names = ['A0:', 'A', 'A0', 'A_', 'A0_', ':A', '0A', '_A']

print(f"Pattern: {pattern}")
for name in test_names:
    match = re.match(pattern, name)
    print(f"  '{name}': match={match is not None}")
    if match:
        print(f"    Matched: '{match.group()}'")

# Test the actual function
print("\nTesting with actual function:")
for name in test_names:
    try:
        result = validate_variables_name({name: "value"})
        print(f"  '{name}': PASSED")
    except ValueError as e:
        print(f"  '{name}': FAILED - {e}")

# The bug is that the pattern doesn't have anchors!
print("\n=== Analysis ===")
print("The regex pattern lacks ^ and $ anchors in the re.match() call")
print("re.match() only matches at the beginning, but doesn't require full match")
print("So 'A0:' matches because 'A0' at the beginning matches the pattern")