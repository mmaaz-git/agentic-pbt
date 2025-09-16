#!/usr/bin/env python3
"""Verify the is_same_domain bug through logical analysis."""

# Let's trace through the is_same_domain logic for pattern="."
# From pyramid/util.py lines 621-637:

def is_same_domain_logic(host, pattern):
    """
    Reimplementation of is_same_domain to trace the logic.
    """
    if not pattern:
        return False
    
    pattern = pattern.lower()
    
    # The problematic logic:
    result = (
        pattern[0] == "."  # True when pattern="."
        and (host.endswith(pattern) or host == pattern[1:])  # This is the issue!
        or pattern == host
    )
    return result

# When pattern = "."
# - pattern[0] == "." → True
# - pattern[1:] → "" (empty string)
# - host.endswith(".") → False for most hosts
# - host == "" → False for non-empty hosts
# - So we get: True and (False or False) or False → False

# Wait, let me check the actual implementation more carefully...
# The code is:
#     return (
#         pattern[0] == "."
#         and (host.endswith(pattern) or host == pattern[1:])
#         or pattern == host
#     )

print("Analyzing is_same_domain logic for pattern='.':")
print("=" * 60)

def analyze_logic(host, pattern):
    """Analyze the is_same_domain logic step by step."""
    print(f"\nHost: '{host}', Pattern: '{pattern}'")
    
    if not pattern:
        print("  Pattern is empty/None → False")
        return False
    
    pattern_lower = pattern.lower()
    print(f"  Pattern (lowercase): '{pattern_lower}'")
    
    # Check conditions
    cond1 = pattern_lower[0] == "."
    print(f"  pattern[0] == '.': {cond1}")
    
    if cond1:
        cond2a = host.endswith(pattern_lower)
        cond2b = host == pattern_lower[1:]
        print(f"  host.endswith(pattern): {cond2a}")
        print(f"  host == pattern[1:]: {cond2b} (pattern[1:] = '{pattern_lower[1:]}')")
        print(f"  Combined: {cond1} and ({cond2a} or {cond2b}) = {cond1 and (cond2a or cond2b)}")
    
    cond3 = pattern_lower == host
    print(f"  pattern == host: {cond3}")
    
    # Final result
    if pattern_lower[0] == ".":
        result = (cond1 and (cond2a or cond2b)) or cond3
    else:
        result = cond3
    
    print(f"  Final result: {result}")
    return result

# Test cases
test_cases = [
    ("example.com", "."),
    ("", "."),
    ("a", "."),
    (".", "."),
    ("example.com", ".com"),
    ("test.com", ".com"),
]

for host, pattern in test_cases:
    analyze_logic(host, pattern)

print("\n" + "=" * 60)
print("CONCLUSION:")
print("When pattern = '.':")
print("  - pattern[1:] = '' (empty string)")  
print("  - 'example.com'.endswith('.') = False")
print("  - 'example.com' == '' = False")
print("  - So the condition fails correctly!")
print("\nActually, let me check if endswith works differently...")

# Check endswith behavior
print("\nChecking str.endswith behavior:")
print(f"  'example.com'.endswith('.') = {'example.com'.endswith('.')}")
print(f"  'example.com'.endswith('') = {'example.com'.endswith('')}")
print(f"  'example.com'.endswith('.com') = {'example.com'.endswith('.com')}")

# Oh wait! I need to check if the host is also lowercased!
print("\nActually checking full is_same_domain implementation:")

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
from pyramid.util import is_same_domain

print(f"  is_same_domain('example.com', '.') = {is_same_domain('example.com', '.')}")
print(f"  is_same_domain('', '.') = {is_same_domain('', '.')}")
print(f"  is_same_domain('a', '.') = {is_same_domain('a', '.')}")

# The bug is real! Pattern '.' matches any non-empty host!