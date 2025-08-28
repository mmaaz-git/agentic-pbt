"""Investigate if pinv bug is real or numerical precision issue."""

import numpy as np
import scipy.linalg


def check_moore_penrose(A, name=""):
    """Check Moore-Penrose conditions with different tolerances."""
    A_pinv = scipy.linalg.pinv(A)
    
    print(f"\n{name}")
    print(f"Matrix shape: {A.shape}, rank: {np.linalg.matrix_rank(A)}")
    print(f"Condition number: {np.linalg.cond(A)}")
    
    # Check conditions with different tolerances
    tolerances = [1e-15, 1e-12, 1e-9, 1e-6]
    
    for tol in tolerances:
        print(f"\nWith tolerance {tol}:")
        
        # Condition 3: (A @ A_pinv) is Hermitian
        product3 = A @ A_pinv
        cond3 = np.allclose(product3, product3.T, rtol=tol, atol=tol)
        max_diff3 = np.max(np.abs(product3 - product3.T))
        print(f"  Condition 3 (A @ A_pinv symmetric): {cond3}, max diff: {max_diff3:.2e}")
        
        # Condition 4: (A_pinv @ A) is Hermitian
        product4 = A_pinv @ A
        cond4 = np.allclose(product4, product4.T, rtol=tol, atol=tol)
        max_diff4 = np.max(np.abs(product4 - product4.T))
        print(f"  Condition 4 (A_pinv @ A symmetric): {cond4}, max diff: {max_diff4:.2e}")


# Test 1: Clean small values 
print("=" * 60)
print("Test 1: Matrix with small but clean value (1e-6)")
A1 = np.array([[0.0, 0.0, 0.0],
               [0.0, 13.0, 1.0],
               [0.0, 1e-6, 0.0]])
check_moore_penrose(A1, "Small value 1e-6")

# Test 2: Even smaller value
print("\n" + "=" * 60)
print("Test 2: Matrix with smaller value (1e-10)")
A2 = np.array([[0.0, 0.0, 0.0],
               [0.0, 13.0, 1.0],
               [0.0, 1e-10, 0.0]])
check_moore_penrose(A2, "Smaller value 1e-10")

# Test 3: Matrix without small values
print("\n" + "=" * 60)
print("Test 3: Matrix with no small values")
A3 = np.array([[0.0, 0.0, 0.0],
               [0.0, 13.0, 1.0],
               [0.0, 0.01, 0.0]])
check_moore_penrose(A3, "No small values (0.01)")

# Test 4: Well-conditioned matrix
print("\n" + "=" * 60)
print("Test 4: Well-conditioned matrix")
A4 = np.array([[1.0, 2.0, 3.0],
               [4.0, 5.0, 6.0],
               [7.0, 8.0, 10.0]])
check_moore_penrose(A4, "Well-conditioned")

# Test 5: Original failing value
print("\n" + "=" * 60)
print("Test 5: Original failing value")
A5 = np.array([[0.0, 0.0, 0.0],
               [0.0, 13.0, 1.0],
               [0.0, 1.91461479e-06, 0.0]])
check_moore_penrose(A5, "Original failing value")

# Test with different cutoff values
print("\n" + "=" * 60)
print("Testing different rcond values for pinv:")
A = A5
for rcond in [1e-15, 1e-12, 1e-10, 1e-8, 1e-6]:
    A_pinv = scipy.linalg.pinv(A, rtol=rcond)
    product3 = A @ A_pinv
    max_diff = np.max(np.abs(product3 - product3.T))
    is_symmetric = np.allclose(product3, product3.T, rtol=1e-9, atol=1e-9)
    print(f"rcond={rcond:.0e}: symmetry error = {max_diff:.2e}, passes test: {is_symmetric}")