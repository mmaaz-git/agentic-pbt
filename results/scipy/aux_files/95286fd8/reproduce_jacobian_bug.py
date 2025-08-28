"""Reproduce jacobian dimension bug in scipy.odr"""

import numpy as np
import scipy.odr as odr

# Test case from the failing test
beta = np.array([0.0, 0.0, 0.0])
x = 0.0
x_arr = np.array([x])

print("Testing quadratic model jacobian...")
print("Beta:", beta)
print("x:", x_arr)

# Get analytical jacobian
print("\nCalling quadratic.fjacb...")
analytical_jac = odr.quadratic.fjacb(beta, x_arr)
print("Analytical jacobian shape:", analytical_jac.shape)
print("Analytical jacobian:")
print(analytical_jac)

# The issue in the test was with indexing
print("\nTrying to access jacobian elements...")
try:
    for i in range(3):
        print(f"analytical_jac[:, {i}] = {analytical_jac[:, i]}")
except IndexError as e:
    print(f"ERROR accessing column {i}: {e}")
    
# Check what the expected shape should be
print("\nExpected behavior:")
print("For n data points and m parameters, fjacb should return (n, m) array")
print(f"We have {len(x_arr)} data points and 3 parameters")
print(f"So shape should be ({len(x_arr)}, 3)")
print(f"Actual shape: {analytical_jac.shape}")

# Check if this is the actual issue
if analytical_jac.shape != (len(x_arr), 3):
    print("\nBUG FOUND: Jacobian has wrong shape!")
    print(f"Expected: ({len(x_arr)}, 3)")
    print(f"Got: {analytical_jac.shape}")

# Test with multiple data points
print("\n\nTesting with multiple data points...")
x_multi = np.array([0.0, 1.0, 2.0])
jac_multi = odr.quadratic.fjacb(beta, x_multi)
print(f"x shape: {x_multi.shape}")
print(f"Jacobian shape: {jac_multi.shape}")
print("Jacobian:")
print(jac_multi)