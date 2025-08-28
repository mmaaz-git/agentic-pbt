import scipy.special as sp
import numpy as np

# Minimal reproduction of the bug
a, b, x = 1.0, 54.0, 0.5
y = sp.betainc(a, b, x)
x_recovered = sp.betaincinv(a, b, y)

print(f"Input x: {x}")
print(f"betainc({a}, {b}, {x}) = {y}")
print(f"betaincinv({a}, {b}, {y}) = {x_recovered}")
print(f"Expected x_recovered: {x}")
print(f"Error: {abs(x_recovered - x)}")

# The issue is that betainc returns 1.0 for many inputs due to precision limits
print("\nShowing multiple inputs mapping to 1.0:")
for test_x in [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    y = sp.betainc(a, b, test_x) 
    print(f"  betainc({a}, {b}, {test_x}) = {y}")

print(f"\nSince all these map to 1.0, betaincinv({a}, {b}, 1.0) can only return one value: {sp.betaincinv(a, b, 1.0)}")