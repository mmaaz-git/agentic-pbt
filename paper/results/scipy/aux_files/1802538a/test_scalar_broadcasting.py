import numpy as np
import scipy.sparse as sp

print("Testing scalar broadcasting in sp.diags")
print("=" * 60)

# Test 1: Single scalar value (should broadcast according to docs)
print("Test 1: Scalar broadcasting")
scalar_value = 5.0
shape = (4, 4)
offset = 0

print(f"sp.diags({scalar_value}, offsets={offset}, shape={shape}):")
try:
    result = sp.diags(scalar_value, offsets=offset, shape=shape)
    print("Success!")
    print(result.toarray())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Test 2: List with single element (should broadcast?)")
single_element_list = [5.0]
print(f"sp.diags({single_element_list}, offsets={offset}, shape={shape}):")
try:
    result = sp.diags(single_element_list, offsets=offset, shape=shape)
    print("Success!")
    print(result.toarray())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Test 3: Multiple diagonals with scalars")
# From the documentation example
diagonals = [1, -2, 1]
offsets = [-1, 0, 1]
shape = (4, 4)
print(f"sp.diags({diagonals}, offsets={offsets}, shape={shape}):")
try:
    result = sp.diags(diagonals, offsets=offsets, shape=shape)
    print("Success!")
    print(result.toarray())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Test 4: Non-scalar list that's too short")
diag_values = [1.0, 2.0]  # Length 2
shape = (4, 4)  # Main diagonal should have length 4
offset = 0
print(f"sp.diags({diag_values}, offsets={offset}, shape={shape}):")
try:
    result = sp.diags(diag_values, offsets=offset, shape=shape)
    print("Success!")
    print(result.toarray())
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Conclusion:")
print("- Scalar values DO broadcast when shape is specified")
print("- Lists with single elements also broadcast")
print("- But lists with 2+ elements must match diagonal length exactly")