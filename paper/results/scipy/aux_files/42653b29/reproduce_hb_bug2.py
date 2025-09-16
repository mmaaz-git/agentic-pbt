"""Reproduce Harwell-Boeing read error bug."""

import scipy.io
import scipy.sparse
import numpy as np
import tempfile
import os

# Create the specific matrix that causes issues
matrix_data = [[0.0, 0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 0.0, 0.0],
               [0.0, 0.0, 0.0, 1.0, -1.360386181804678e-192]]

matrix = scipy.sparse.csr_matrix(np.array(matrix_data))

print("Matrix to write:")
print(matrix.toarray())
print(f"Matrix shape: {matrix.shape}")
print(f"Non-zero elements: {matrix.nnz}")

# Try to write and read it
with tempfile.NamedTemporaryFile(suffix='.hb', delete=False) as f:
    filename = f.name

try:
    scipy.io.hb_write(filename, matrix)
    print("Write succeeded")
    
    # Try to read it back
    read_matrix = scipy.io.hb_read(filename)
    print("Read succeeded")
    print("Read matrix:")
    print(read_matrix.toarray())
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Error type: {type(e).__name__}")
finally:
    if os.path.exists(filename):
        os.unlink(filename)