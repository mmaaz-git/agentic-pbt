import numpy as np
import warnings
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Test matrix multiplication with 1D array behavior
m = np.matrix([[1, 2], [3, 4]])
arr = np.array([5, 6])

print("Matrix shape:", m.shape)
print("Array shape:", arr.shape)
print("Array as is:", arr)

# What happens when we convert 1D array to matrix?
arr_as_matrix = np.asmatrix(arr)
print("\nArray converted to matrix via asmatrix:")
print("Shape:", arr_as_matrix.shape)
print("Value:", arr_as_matrix)

# Try multiplication
try:
    result = m * arr
    print("\nDirect multiplication m * arr succeeded:")
    print("Result shape:", result.shape)
    print("Result:", result)
except ValueError as e:
    print(f"\nDirect multiplication m * arr failed: {e}")

# Try with different array orientations
col_arr = arr.reshape(-1, 1)
print(f"\nColumn array shape: {col_arr.shape}")
result = m * col_arr
print(f"m * col_arr result shape: {result.shape}")
print(f"Result: {result}")

# What about row array?
row_arr = arr.reshape(1, -1)
print(f"\nRow array shape: {row_arr.shape}")
try:
    result = m * row_arr
    print(f"m * row_arr succeeded")
except ValueError as e:
    print(f"m * row_arr failed: {e}")

# Test the documented behavior from the code
print("\n--- Testing behavior described in matrix.__mul__ ---")
print("From the code: 'This promotes 1-D vectors to row vectors'")

# Let's see what asmatrix does with 1D array
print("\nTesting asmatrix on 1D array:")
test_1d = np.array([1, 2, 3])
mat_1d = np.asmatrix(test_1d)
print(f"1D array {test_1d} with shape {test_1d.shape}")
print(f"Becomes matrix with shape {mat_1d.shape}: {mat_1d}")

# This reveals the issue: 1D arrays are promoted to ROW vectors (1, n), not column vectors!
# For matrix multiplication A * B, we need A.shape[1] == B.shape[0]
# But if B is 1D and gets promoted to (1, n), the multiplication fails!

print("\n--- Confirming the bug ---")
A = np.matrix([[1, 2], [3, 4]])  # Shape (2, 2)
b = np.array([5, 6])  # Shape (2,)

print(f"Matrix A shape: {A.shape}")
print(f"Vector b shape: {b.shape}")

# According to the comment in __mul__, this should promote b to row vector
b_promoted = np.asmatrix(b)
print(f"b promoted to matrix: shape {b_promoted.shape}")
print(f"For A*b to work, we need A.shape[1] ({A.shape[1]}) == b_promoted.shape[0] ({b_promoted.shape[0]})")
print(f"But we have: {A.shape[1]} != {b_promoted.shape[0]}")

# The expected mathematical behavior would be to treat 1D as column vector
print("\nExpected behavior (treating 1D as column):")
b_col = b.reshape(-1, 1)
result = A * b_col
print(f"A * b_column = {result.flatten()}")

# But the actual implementation treats it as row
print("\nActual implementation:")
try:
    result = A * b
    print(f"A * b = {result}")
except ValueError as e:
    print(f"A * b fails with: {e}")
    print("This is because b is promoted to row vector (1, 2), not column vector (2, 1)")

# Testing list and tuple inputs
print("\n--- Testing with list and tuple ---")
list_input = [5, 6]
tuple_input = (5, 6)

for inp, name in [(list_input, "list"), (tuple_input, "tuple")]:
    try:
        result = A * inp
        print(f"A * {name} succeeded: {result}")
    except ValueError as e:
        print(f"A * {name} failed: {e}")