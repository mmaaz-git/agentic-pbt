"""
Minimal reproduction of typeof bug in Cython.Shadow module.
"""
import Cython.Shadow as Shadow

# The bug: typeof returns string names instead of actual type objects
print("Bug demonstration: typeof returns strings, not type objects\n")

# Test with various Python types
test_values = [
    42,           # int
    3.14,         # float
    "hello",      # str
    [1, 2, 3],    # list
    {"a": 1},     # dict
    (1, 2),       # tuple
    {1, 2, 3},    # set
    None,         # NoneType
    True,         # bool
]

print("Value\t\ttypeof(value)\t\ttype(value)")
print("-" * 60)

for value in test_values:
    typeof_result = Shadow.typeof(value)
    actual_type = type(value)
    
    # Show the value (truncated if too long)
    value_str = str(value)[:15]
    
    print(f"{value_str:15}\t{typeof_result!r:20}\t{actual_type}")

print("\nProblem:")
print("1. typeof() returns string representations like 'int', 'float'")
print("2. Expected: return actual type objects like int, float")
print("3. This breaks any code expecting: isinstance(Shadow.typeof(x), type)")

# Demonstrate the issue more clearly
print("\nComparison:")
x = 42
print(f"Shadow.typeof({x}) == int  → {Shadow.typeof(x) == int}  (FAILS)")
print(f"Shadow.typeof({x}) == 'int' → {Shadow.typeof(x) == 'int'}  (Actual behavior)")
print(f"type({x}) == int           → {type(x) == int}  (Expected behavior)")

# Check if this might be intentional
print("\nChecking if this might be intentional...")
print(f"Is typeof result a string? {isinstance(Shadow.typeof(42), str)}")
print(f"Is typeof result a type?   {isinstance(Shadow.typeof(42), type)}")