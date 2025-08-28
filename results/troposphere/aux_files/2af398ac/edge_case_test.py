#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean, integer, double
import math

print("=== Testing edge cases for validators ===\n")

# Edge case 1: What about string "1" for boolean? The code checks for "1" in the list 
print("Edge case: String '1' for boolean")
result = boolean("1")
print(f"  boolean('1') = {result}")

# Edge case 2: Does integer handle float inputs without decimal part?
print("\nEdge case: Float 1.0 for integer")
try:
    result = integer(1.0)
    print(f"  integer(1.0) = {result}")
except ValueError as e:
    print(f"  integer(1.0) raised ValueError: {e}")

# Edge case 3: Special float values
print("\nEdge case: Special float values for double")
special_floats = [float('inf'), float('-inf'), float('nan')]
for val in special_floats:
    try:
        result = double(val)
        print(f"  double({val}) = {result}")
    except ValueError as e:
        print(f"  double({val}) raised ValueError: {e}")

# Edge case 4: Empty string
print("\nEdge case: Empty string")
for func_name, func in [("boolean", boolean), ("integer", integer), ("double", double)]:
    try:
        result = func("")
        print(f"  {func_name}('') = {result}")
    except ValueError as e:
        print(f"  {func_name}('') raised ValueError")

# Edge case 5: Scientific notation for double
print("\nEdge case: Scientific notation for double")
scientific = ["1e5", "3.14e-2", "-2.5e3"]
for val in scientific:
    try:
        result = double(val)
        print(f"  double('{val}') = {result}")
    except ValueError as e:
        print(f"  double('{val}') raised ValueError: {e}")

# Edge case 6: Boolean with "1" vs 1
print("\nComparing boolean('1') and boolean(1)")
print(f"  boolean('1') == boolean(1): {boolean('1') == boolean(1)}")
print(f"  boolean('1') is boolean(1): {boolean('1') is boolean(1)}")

# Edge case 7: Large numbers
print("\nEdge case: Very large numbers")
large_int = 10**100
large_str = str(large_int)
try:
    result = integer(large_str)
    print(f"  integer('{large_str[:20]}...') = {result[:20] if isinstance(result, str) else result}")
except Exception as e:
    print(f"  integer(large) raised: {e}")

# Edge case 8: Check the actual implementation details
print("\nChecking implementation...")
print(f"  boolean(1) returns type: {type(boolean(1))}")
print(f"  boolean(True) returns type: {type(boolean(True))}")
print(f"  integer(5) returns type: {type(integer(5))}")
print(f"  integer('5') returns type: {type(integer('5'))}")
print(f"  double(5.5) returns type: {type(double(5.5))}")
print(f"  double('5.5') returns type: {type(double('5.5'))}")