import numpy as np
import warnings

warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

print("Testing matrix string parsing with boolean and None values")
print("=" * 60)

# Test cases with boolean values
test_cases = [
    ("True False; False True", "Boolean values"),
    ("1 True; False 0", "Mixed numeric and boolean"),
    ("None 1; 2 3", "None with numbers"),
    ("True", "Single True"),
    ("False", "Single False"),
    ("None", "Single None"),
    ("True False True; False True False", "Multiple booleans"),
]

for input_str, description in test_cases:
    print(f"\n{description}:")
    print(f"  Input: '{input_str}'")
    try:
        m = np.matrix(input_str)
        print(f"  Result shape: {m.shape}")
        print(f"  Result dtype: {m.dtype}")
        print(f"  Result values: {m.tolist()}")
        
        # Check if boolean values are preserved or converted
        if 'True' in input_str or 'False' in input_str:
            print(f"  Boolean conversion: True -> {m[m == 1].size > 0 if 'True' in input_str else 'N/A'}")
            print(f"                      False -> {m[m == 0].size > 0 if 'False' in input_str else 'N/A'}")
            
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("The matrix string parser converts boolean literals to numbers:")
print("- True becomes 1")
print("- False becomes 0")
print("- None becomes... let's check:")

# Special test for None
print("\nDetailed None test:")
m = np.matrix("None 2; 3 4")
print(f"Matrix with None: {m}")
print(f"Type of first element: {type(m[0, 0])}")
print(f"Value of first element: {m[0, 0]}")
print(f"Is it actually None? {m[0, 0] is None}")

# The bug: None is stored as object dtype
print("\n" + "=" * 60)
print("BUG DISCOVERED:")
print("When parsing 'None' in a matrix string, it creates an object array")
print("This can lead to unexpected behavior:")

# Demonstrate the issue
m1 = np.matrix("None 1; 2 3")
m2 = np.matrix("4 5; 6 7")

print(f"\nm1 (with None): dtype={m1.dtype}, values={m1.tolist()}")
print(f"m2 (normal): dtype={m2.dtype}, values={m2.tolist()}")

try:
    result = m1 + m2
    print(f"\nm1 + m2 = {result}")
except Exception as e:
    print(f"\nm1 + m2 raises: {type(e).__name__}: {e}")
    print("*** BUG: Cannot perform arithmetic on matrix with None ***")

# Try multiplication
try:
    result = m1 * m2
    print(f"\nm1 * m2 = {result}")
except Exception as e:
    print(f"\nm1 * m2 raises: {type(e).__name__}: {e}")
    print("*** BUG: Cannot perform matrix multiplication with None ***")

# More edge cases
print("\n" + "=" * 60)
print("ADDITIONAL EDGE CASES:")

# What about empty string literals?
test_cases_2 = [
    ("''", "Empty string literal"),
    ('""', "Empty double-quoted string"),
    ("'hello'", "String literal"),
    ("[]", "Empty list literal"),
    ("{}", "Empty dict literal"),
    ("()", "Empty tuple literal"),
]

for input_str, description in test_cases_2:
    print(f"\n{description}: '{input_str}'")
    try:
        m = np.matrix(input_str)
        print(f"  Success: dtype={m.dtype}, value={m[0, 0]}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")

# The real issue with mixed types
print("\n" + "=" * 60)
print("MIXED TYPE MATRIX BUG:")

m = np.matrix("1 'text'; None True")
print(f"Mixed type matrix: {m}")
print(f"dtype: {m.dtype}")
print(f"Values: {m.tolist()}")
print("\nThis creates an object array that breaks mathematical operations!")