"""Reproduce Harwell-Boeing zero matrix bug."""

import scipy.io
import scipy.sparse
import numpy as np
import tempfile

# Create a matrix with all zeros
matrix = scipy.sparse.csr_matrix(np.array([[0.0, 0.0], [0.0, 0.0]]))

print("Matrix to write:")
print(matrix.toarray())
print(f"Matrix shape: {matrix.shape}")
print(f"Non-zero elements: {matrix.nnz}")

# Try to write it
with tempfile.NamedTemporaryFile(suffix='.hb', delete=False) as f:
    filename = f.name

try:
    scipy.io.hb_write(filename, matrix)
    print("Write succeeded")
except Exception as e:
    print(f"Error during write: {e}")
    print(f"Error type: {type(e).__name__}")