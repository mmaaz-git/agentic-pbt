"""
Minimal reproduction of the None parsing bug in numpy.matrixlib
"""
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Reproduce the bug
print("BUG: numpy.matrix string parser accepts 'None' creating unusable matrices")
print("=" * 70)

# Create a matrix with None
m1 = np.matrix("None 2; 3 4")
print(f"m1 = np.matrix('None 2; 3 4')")
print(f"Result: {m1}")
print(f"dtype: {m1.dtype}")

# Try to use it in computation
m2 = np.matrix("5 6; 7 8")
print(f"\nm2 = np.matrix('5 6; 7 8')")
print(f"Result: {m2}")

# Addition fails
print("\nAttempting m1 + m2:")
try:
    result = m1 + m2
    print(f"Result: {result}")
except TypeError as e:
    print(f"ERROR: {e}")
    
# Multiplication fails
print("\nAttempting m1 * m2:")
try:
    result = m1 * m2
    print(f"Result: {result}")
except TypeError as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 70)
print("WHY THIS IS A BUG:")
print("1. The string 'None' is parsed as Python's None object, not a number")
print("2. This creates an object dtype matrix that cannot be used mathematically")
print("3. No warning or error is raised during parsing")
print("4. The user likely meant to input a number, not None")
print("5. This violates the principle that matrices should contain numeric data")