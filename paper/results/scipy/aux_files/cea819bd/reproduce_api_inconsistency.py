"""Minimal reproduction of API inconsistency in scipy.differentiate"""

import numpy as np
from scipy import differentiate

# Define a simple test function
def f_scalar(x):
    """Scalar function for derivative"""
    return x**2

def f_vector(x):
    """Vector function for jacobian"""
    return np.array([x[0]**2, x[1]**2])

def f_scalar_multivar(x):
    """Scalar multivariate function for hessian"""
    return x[0]**2 + x[1]**2

# Test derivative - returns 'df' attribute
x_scalar = 1.0
res_derivative = differentiate.derivative(f_scalar, x_scalar)
print("derivative result attributes:", [attr for attr in dir(res_derivative) if not attr.startswith('_')])
print("  Has 'df'?:", hasattr(res_derivative, 'df'))
print("  Value of derivative:", res_derivative.df)

# Test jacobian - returns 'df' attribute  
x_vector = np.array([1.0, 2.0])
res_jacobian = differentiate.jacobian(f_vector, x_vector)
print("\njacobian result attributes:", [attr for attr in dir(res_jacobian) if not attr.startswith('_')])
print("  Has 'df'?:", hasattr(res_jacobian, 'df'))
print("  Value of Jacobian:\n", res_jacobian.df)

# Test hessian - returns 'ddf' attribute (INCONSISTENT!)
res_hessian = differentiate.hessian(f_scalar_multivar, x_vector)
print("\nhessian result attributes:", [attr for attr in dir(res_hessian) if not attr.startswith('_')])
print("  Has 'df'?:", hasattr(res_hessian, 'df'))
print("  Has 'ddf'?:", hasattr(res_hessian, 'ddf'))
print("  Value of Hessian:\n", res_hessian.ddf)

print("\n" + "="*60)
print("BUG: API Inconsistency Detected!")
print("="*60)
print("- derivative() returns result with 'df' attribute")
print("- jacobian() returns result with 'df' attribute")  
print("- hessian() returns result with 'ddf' attribute (inconsistent!)")
print("\nAdditionally, documentation at line 1036 incorrectly refers to 'dff' instead of 'ddf'")