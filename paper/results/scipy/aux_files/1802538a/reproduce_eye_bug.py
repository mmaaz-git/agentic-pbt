import numpy as np
import scipy.sparse as sp

# Minimal reproduction of the eye bug
print("Testing sp.eye with various k values")
print("=" * 60)

# Test case 1: Regular eye matrix
n = 3
k = 0
print(f"sp.eye({n}, k={k}):")
result = sp.eye(n, k=k)
print(result.toarray())

# Test case 2: Upper diagonal
k = 1
print(f"\nsp.eye({n}, k={k}):")
result = sp.eye(n, k=k)
print(result.toarray())

# Test case 3: Lower diagonal
k = -1
print(f"\nsp.eye({n}, k={k}):")
result = sp.eye(n, k=k)
print(result.toarray())

# Test case 4: k out of bounds
print("\n" + "=" * 60)
print("Testing edge cases:")
n = 2
k = -19  # This was from our failing test

print(f"\nTrying sp.eye({n}, k={k}):")
try:
    result = sp.eye(n, k=k)
    print("Success! Result shape:", result.shape)
    print(result.toarray())
except Exception as e:
    print(f"ERROR: {e}")

# Let's trace the error more carefully
print("\n" + "=" * 60)
print("The issue seems to be when k is far outside the matrix bounds")
print("Let's test with reasonable k values relative to matrix size")

for n in [3, 5]:
    for k in range(-n+1, n):
        try:
            result = sp.eye(n, k=k)
            diag = np.diag(result.toarray(), k=k)
            if not np.all(diag == 1.0):
                print(f"ISSUE: sp.eye({n}, k={k}) diagonal not all ones!")
        except Exception as e:
            print(f"ERROR at sp.eye({n}, k={k}): {e}")