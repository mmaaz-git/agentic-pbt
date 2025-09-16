"""Reproduce polynomial factory API bug in scipy.odr"""

import numpy as np
import scipy.odr as odr

# Create polynomial model
print("Creating polynomial of degree 2...")
poly = odr.polynomial(2)
print("Type:", type(poly))
print("Is Model instance:", isinstance(poly, odr.Model))

# Test with coefficients and data
beta = np.array([1.0, 2.0, 3.0])  # 3 coefficients for degree 2
x = np.array([0.0, 1.0, 2.0])

print("\nTrying to evaluate polynomial directly...")
try:
    result = poly.fcn(beta, x)
    print("Success! Result:", result)
except TypeError as e:
    print("ERROR:", e)
    
print("\nChecking function signature...")
import inspect
sig = inspect.signature(poly.fcn)
print("Signature:", sig)

print("\nTrying to call with powers argument...")
# Based on the error, it seems to need a 'powers' argument
# Let's check what the polynomial factory docstring says
print("\nPolynomial factory docstring:")
print(odr.polynomial.__doc__[:500])

print("\nLet's check what powers might be...")
# The polynomial factory likely stores powers internally
if hasattr(poly, 'meta'):
    print("poly.meta:", poly.meta)
    
# Try to find the powers
for attr in dir(poly):
    if 'power' in attr.lower():
        print(f"Found attribute: {attr} = {getattr(poly, attr)}")

# Let's check the actual function implementation
print("\nFunction source (if available):")
try:
    source = inspect.getsource(poly.fcn)
    print(source[:500])
except:
    print("Cannot get source")
    
# Try to use the polynomial in an actual ODR fit
print("\nTrying to use polynomial in ODR fit...")
x_data = np.array([0, 1, 2, 3, 4])
y_data = 1 + 2*x_data + 3*x_data**2

data = odr.Data(x_data, y_data)
odr_obj = odr.ODR(data, poly, beta0=[1, 1, 1])
try:
    output = odr_obj.run()
    print("Success! Beta:", output.beta)
except Exception as e:
    print("ERROR during ODR run:", e)