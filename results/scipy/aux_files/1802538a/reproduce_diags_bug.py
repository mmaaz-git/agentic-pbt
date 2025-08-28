import numpy as np
import scipy.sparse as sp

# Minimal reproduction of the diags bug
print("Testing sp.diags with diagonal values shorter than matrix size")
print("=" * 60)

# Case that should work: diagonal values = [0.0, 0.0], offset=0, size=3x3
diag_values = [0.0, 0.0]
offset = 0
size = 3

print(f"Input: diag_values={diag_values}, offset={offset}, shape=({size}, {size})")

try:
    # This is what the documentation suggests should work
    result = sp.diags(diag_values, offset, shape=(size, size))
    print("Success! Result:")
    print(result.toarray())
except ValueError as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("Testing with numpy.diag for comparison")
# How numpy handles this
np_diag = np.diag(diag_values, k=offset)
print(f"np.diag({diag_values}, k={offset}) produces shape {np_diag.shape}:")
print(np_diag)

print("\n" + "=" * 60)
print("Testing sp.diags with full-length diagonal")
full_diag_values = [1.0, 2.0, 3.0]  # Length matches matrix size
result2 = sp.diags(full_diag_values, offset, shape=(size, size))
print(f"sp.diags({full_diag_values}, {offset}, shape=({size}, {size})):")
print(result2.toarray())

print("\n" + "=" * 60)
print("Analysis:")
print("The documentation says diags creates a sparse matrix with values")
print("placed on the specified diagonal. However, it requires the diagonal")
print("values to match the diagonal length, unlike numpy.diag which broadcasts.")