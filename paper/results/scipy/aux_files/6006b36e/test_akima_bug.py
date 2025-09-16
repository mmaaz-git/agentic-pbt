import numpy as np
from scipy import interpolate

# Minimal reproduction of Akima1DInterpolator bug with 2 points
x = np.array([0., 0.01])
y = np.array([671089.0857770094, 0.0])

print("Testing Akima1DInterpolator with 2 points")
print("Input x:", x)
print("Input y:", y)

try:
    akima = interpolate.Akima1DInterpolator(x, y)
    result = akima(x)
    
    print("Akima result:", result)
    print("Expected:    ", y)
    print("Difference:  ", result - y)
    
    if not np.allclose(result, y, rtol=1e-10, atol=1e-10):
        print("\n❌ BUG: Akima1DInterpolator doesn't pass through given points!")
        print(f"At x={x[1]}, expected y={y[1]}, but got {result[1]}")
    else:
        print("\n✅ No bug found")
except Exception as e:
    print(f"\n⚠️ Exception raised: {e}")
    print("This might be expected behavior if Akima requires more points")