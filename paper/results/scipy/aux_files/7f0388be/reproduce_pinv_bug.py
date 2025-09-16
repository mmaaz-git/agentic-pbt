"""Minimal reproduction of scipy.linalg.pinv bug."""

import numpy as np
import scipy.linalg


def test_moore_penrose_conditions(A):
    """Test all four Moore-Penrose conditions for the pseudo-inverse."""
    A_pinv = scipy.linalg.pinv(A)
    
    print(f"Testing matrix A with shape {A.shape}:")
    print(A)
    print(f"\nPseudo-inverse A_pinv:")
    print(A_pinv)
    
    # Test the four Moore-Penrose conditions
    # 1. A @ A_pinv @ A = A
    result1 = A @ A_pinv @ A
    cond1_satisfied = np.allclose(result1, A, rtol=1e-9, atol=1e-9)
    print(f"\nCondition 1 (A @ A_pinv @ A = A): {cond1_satisfied}")
    if not cond1_satisfied:
        print(f"  Max difference: {np.max(np.abs(result1 - A))}")
    
    # 2. A_pinv @ A @ A_pinv = A_pinv
    result2 = A_pinv @ A @ A_pinv
    cond2_satisfied = np.allclose(result2, A_pinv, rtol=1e-9, atol=1e-9)
    print(f"Condition 2 (A_pinv @ A @ A_pinv = A_pinv): {cond2_satisfied}")
    if not cond2_satisfied:
        print(f"  Max difference: {np.max(np.abs(result2 - A_pinv))}")
    
    # 3. (A @ A_pinv) is Hermitian
    product3 = A @ A_pinv
    cond3_satisfied = np.allclose(product3, product3.T, rtol=1e-9, atol=1e-9)
    print(f"Condition 3 (A @ A_pinv is Hermitian): {cond3_satisfied}")
    if not cond3_satisfied:
        print(f"  Max difference: {np.max(np.abs(product3 - product3.T))}")
    
    # 4. (A_pinv @ A) is Hermitian  
    product4 = A_pinv @ A
    cond4_satisfied = np.allclose(product4, product4.T, rtol=1e-9, atol=1e-9)
    print(f"Condition 4 (A_pinv @ A is Hermitian): {cond4_satisfied}")
    if not cond4_satisfied:
        print(f"  Max difference: {np.max(np.abs(product4 - product4.T))}")
    
    return cond1_satisfied and cond2_satisfied and cond3_satisfied and cond4_satisfied


# Test case 1: From the failing test
print("=" * 60)
print("Test Case 1: Matrix with many zeros")
A1 = np.array([[0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                0.00000000e+00, 0.00000000e+00],
               [0.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                0.00000000e+00, 1.00000000e+00],
               [1.00000000e+00, 0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                0.00000000e+00, 0.00000000e+00],
               [2.00000000e+00, 1.91461479e-06, 0.00000000e+00, 0.00000000e+00,
                0.00000000e+00, 7.00000000e+00]])
all_satisfied1 = test_moore_penrose_conditions(A1)
print(f"\nAll conditions satisfied: {all_satisfied1}")

# Test case 2: Simpler failing case
print("\n" + "=" * 60)
print("Test Case 2: Simpler failing case")
A2 = np.array([[0.0, 0.0, 6.0],
               [1.0, 0.0, 0.0],
               [1.0, 0.0, 0.0],
               [1.0, 1.91461479e-06, 0.0]])
all_satisfied2 = test_moore_penrose_conditions(A2)
print(f"\nAll conditions satisfied: {all_satisfied2}")

# Test case 3: Even simpler case
print("\n" + "=" * 60)
print("Test Case 3: Even simpler failing case")
A3 = np.array([[0.0, 0.0, 0.0],
               [0.0, 13.0, 1.0],
               [0.0, 1.91461479e-06, 0.0]])
all_satisfied3 = test_moore_penrose_conditions(A3)
print(f"\nAll conditions satisfied: {all_satisfied3}")

# Compare with numpy's pinv
print("\n" + "=" * 60)
print("Comparison with NumPy's pinv for Test Case 3:")
A = A3
scipy_pinv = scipy.linalg.pinv(A)
numpy_pinv = np.linalg.pinv(A)

print(f"\nscipy.linalg.pinv result:")
print(scipy_pinv)
print(f"\nnumpy.linalg.pinv result:")
print(numpy_pinv)
print(f"\nDifference between scipy and numpy pinv:")
print(f"Max difference: {np.max(np.abs(scipy_pinv - numpy_pinv))}")

# Test numpy's implementation
print("\nTesting NumPy's pinv with Moore-Penrose conditions:")
A_pinv_numpy = numpy_pinv

# Test conditions for numpy
result1 = A @ A_pinv_numpy @ A
cond1_np = np.allclose(result1, A, rtol=1e-9, atol=1e-9)
print(f"Condition 1 (numpy): {cond1_np}")

result2 = A_pinv_numpy @ A @ A_pinv_numpy
cond2_np = np.allclose(result2, A_pinv_numpy, rtol=1e-9, atol=1e-9)
print(f"Condition 2 (numpy): {cond2_np}")

product3 = A @ A_pinv_numpy
cond3_np = np.allclose(product3, product3.T, rtol=1e-9, atol=1e-9)
print(f"Condition 3 (numpy): {cond3_np}")

product4 = A_pinv_numpy @ A
cond4_np = np.allclose(product4, product4.T, rtol=1e-9, atol=1e-9)
print(f"Condition 4 (numpy): {cond4_np}")