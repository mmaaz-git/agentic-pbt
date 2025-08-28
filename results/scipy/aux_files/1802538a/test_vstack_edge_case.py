import scipy.sparse as sp
import numpy as np

print("Testing vstack edge cases")
print("=" * 60)

# Test 1: Empty list
print("\nTest 1: sp.vstack([])")
try:
    result = sp.vstack([])
    print(f"Result: {result}")
except Exception as e:
    print(f"{type(e).__name__}: {e}")

# Test 2: Single matrix (should work)
print("\nTest 2: sp.vstack([single_matrix])")
m = sp.csr_matrix([[1, 2], [3, 4]])
result = sp.vstack([m])
print(f"Shape: {result.shape}")
print(f"Content:\n{result.toarray()}")

# Test 3: Incompatible shapes
print("\nTest 3: sp.vstack with incompatible column counts")
m1 = sp.csr_matrix([[1, 2]])  # 1x2
m2 = sp.csr_matrix([[3, 4, 5]])  # 1x3
try:
    result = sp.vstack([m1, m2])
    print(f"Result: {result.toarray()}")
except Exception as e:
    print(f"{type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("vstack handles empty list better than hstack (ValueError vs IndexError)")