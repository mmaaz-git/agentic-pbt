import numpy as np
import warnings
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Test cases that cause infinity
test_cases = [
    "1e309",  # Should overflow to inf
    "1e308",  # Borderline
    "1e307",  # Should be OK
    "-1e309",  # Negative inf
    "1e309 2; 3 4",  # Mixed with normal values
    "1e400",  # Very large
    "9.9e307",  # Close to max
    "1.8e308",  # Just over max
]

print("Testing large exponent handling in matrix string parsing:")
print("=" * 60)

for test_str in test_cases:
    try:
        m = np.matrix(test_str)
        print(f"\nInput: '{test_str}'")
        print(f"  Shape: {m.shape}")
        print(f"  Values: {m}")
        print(f"  Contains inf: {np.any(np.isinf(m))}")
        print(f"  All finite: {np.all(np.isfinite(m))}")
        
        # This is the bug: the matrix constructor accepts the string
        # and creates infinity values without warning or error
        if np.any(np.isinf(m)):
            print("  *** BUG: Matrix contains infinity! ***")
            
    except Exception as e:
        print(f"\nInput: '{test_str}'")
        print(f"  Exception: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("The matrix string parser uses ast.literal_eval which can parse")
print("floating point literals like '1e309'. However, when Python")
print("converts these to float, they overflow to infinity.")
print("\nThe bug is that np.matrix() silently accepts these infinity")
print("values when parsing from string, even though it might not be")
print("the user's intention.")

# Demonstrate the issue more clearly
print("\n" + "=" * 60)
print("MINIMAL REPRODUCTION:")
print()
print(">>> import numpy as np")
print(">>> m = np.matrix('1e309')")
print(">>> m")
m = np.matrix('1e309')
print(m)
print(">>> np.isinf(m)")
print(np.isinf(m))
print("\nThe matrix contains infinity, which may not be intended.")
print("Compare with direct float parsing:")
print(">>> float('1e309')")
print(float('1e309'))

# Test with hypothesis
from hypothesis import given, strategies as st, assume

@given(st.integers(min_value=300, max_value=500))
def test_large_exponents_create_infinity(exp):
    """Property: matrix string parsing with large exponents creates infinity"""
    s = f"1e{exp}"
    m = np.matrix(s)
    
    # For exponents >= 309, we expect infinity
    if exp >= 309:
        assert np.isinf(m[0, 0]), f"Expected infinity for 1e{exp}"
    
    # The bug is that this silently succeeds instead of raising an error
    # or at least warning about overflow

print("\n" + "=" * 60)
print("RUNNING PROPERTY TEST:")
test_large_exponents_create_infinity()
print("Property test passed - confirms the bug exists")

# Check if regular matrix construction has same issue
print("\n" + "=" * 60)
print("COMPARISON WITH DIRECT CONSTRUCTION:")
print("\nDirect construction with inf:")
m1 = np.matrix([[float('inf'), 2], [3, 4]])
print(f"np.matrix([[float('inf'), 2], [3, 4]]) works: {m1}")

print("\nDirect construction with 1e309:")
m2 = np.matrix([[1e309, 2], [3, 4]])
print(f"np.matrix([[1e309, 2], [3, 4]]) works: {m2}")
print(f"Contains inf: {np.any(np.isinf(m2))}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("The issue is that when parsing from string, very large numeric")
print("literals (like 1e309) silently overflow to infinity. This could")
print("be considered a bug because:")
print("1. It's silent - no warning or error")
print("2. String input '1e309' looks like a valid finite number") 
print("3. User might not realize they're creating infinity values")
print("4. This behavior is inconsistent with typical numeric overflow handling")