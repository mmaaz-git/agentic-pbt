#!/usr/bin/env python3
"""Simple test to explore Separator behavior."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages")

from InquirerPy.separator import Separator

# Test 1: Default value
print("Test 1: Default value")
sep = Separator()
print(f"  Default separator: '{str(sep)}'")
print(f"  Expected: '---------------'")
print(f"  Match: {str(sep) == '---------------'}")

# Test 2: Custom string
print("\nTest 2: Custom string")
sep2 = Separator("===")
print(f"  Custom separator: '{str(sep2)}'")
print(f"  Expected: '==='")
print(f"  Match: {str(sep2) == '==='}")

# Test 3: Empty string
print("\nTest 3: Empty string")
sep3 = Separator("")
print(f"  Empty separator: '{str(sep3)}'")
print(f"  Expected: ''")
print(f"  Match: {str(sep3) == ''}")

# Test 4: Unicode
print("\nTest 4: Unicode")
sep4 = Separator("🦄🌈")
print(f"  Unicode separator: '{str(sep4)}'")
print(f"  Expected: '🦄🌈'")
print(f"  Match: {str(sep4) == '🦄🌈'}")

# Test 5: None value
print("\nTest 5: None value")
try:
    sep5 = Separator(None)
    print(f"  None separator: '{str(sep5)}'")
    print(f"  Type of result: {type(str(sep5))}")
except Exception as e:
    print(f"  Error: {e}")

# Test 6: Integer value
print("\nTest 6: Integer value")
try:
    sep6 = Separator(123)
    print(f"  Integer separator: '{str(sep6)}'")
    print(f"  Type of result: {type(str(sep6))}")
    print(f"  Value equals input: {str(sep6) == 123}")
except Exception as e:
    print(f"  Error: {e}")

# Test 7: Multiple calls to str()
print("\nTest 7: Multiple calls consistency")
sep7 = Separator("test")
results = [str(sep7) for _ in range(5)]
print(f"  All results: {results}")
print(f"  All same: {all(r == 'test' for r in results)}")

print("\nAll manual tests completed!")