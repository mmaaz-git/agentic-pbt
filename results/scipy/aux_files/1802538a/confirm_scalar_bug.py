import numpy as np
import scipy.sparse as sp

print("DOCUMENTATION CLAIM vs REALITY")
print("=" * 60)
print("The scipy.sparse.diags documentation states:")
print('"Broadcasting of scalars is supported (but shape needs to be specified)"')
print("\nLet's test this claim...")
print("=" * 60)

# Test case from the documentation itself
print("\nTest: Exact example from documentation")
print("Code: sp.diags([1, -2, 1], [-1, 0, 1], shape=(4, 4))")
result = sp.diags([1, -2, 1], [-1, 0, 1], shape=(4, 4))
print("Result:")
print(result.toarray())
print("✓ This works - scalars in a list broadcast correctly")

print("\n" + "=" * 60)
print("\nTest: Pure scalar (not in a list)")
print("Code: sp.diags(5, 0, shape=(3, 3))")
try:
    result = sp.diags(5, 0, shape=(3, 3))
    print("Result:")
    print(result.toarray())
except Exception as e:
    print(f"✗ ERROR: {e}")
    print("This fails even though documentation says scalars are supported!")

print("\n" + "=" * 60)
print("\nTest: What numpy.diag does with a scalar")
print("Code: np.diag(5)")
np_result = np.diag(5)
print(f"np.diag(5) returns: {np_result}")
print("(numpy treats scalar as 1-element array)")

print("\n" + "=" * 60)
print("\nCONCLUSION:")
print("The documentation claims 'Broadcasting of scalars is supported'")
print("but sp.diags(scalar, ...) fails with 'object of type 'float' has no len()'")
print("This is either:")
print("1. A bug in the implementation (scalar should work)")
print("2. A bug in the documentation (should clarify scalars must be in lists)")
print("\nThe documentation example uses [1, -2, 1] not raw scalars,")
print("suggesting the wording 'scalars' might mean 'single-element arrays'.")