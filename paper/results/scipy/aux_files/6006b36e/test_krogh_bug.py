import numpy as np
from scipy import interpolate

# Minimal reproduction of KroghInterpolator bug
x = np.array([0., 1., 6.])
y = np.array([1.0, 91910.0, 0.0])

krogh = interpolate.KroghInterpolator(x, y)
result = krogh(x)

print("Input x:", x)
print("Input y:", y)
print("Krogh result:", result)
print("Expected:    ", y)
print("Difference:  ", result - y)
print("Max abs diff:", np.max(np.abs(result - y)))

# Check if it passes through points
if not np.allclose(result, y, rtol=1e-10, atol=1e-10):
    print("\n❌ BUG: KroghInterpolator doesn't pass through given points!")
    print(f"At x={x[2]}, expected y={y[2]}, but got {result[2]}")
else:
    print("\n✅ No bug found")