import numpy as np
from scipy import interpolate

# Minimal reproduction of RBFInterpolator bug
points = np.array([
    [0.0, 2.0],
    [0.0, 1.5],
    [0.0, 2.2250738585e-313],
    [0.0, 1.0],
    [0.0, 0.0],
    [1.0, 0.0]
])
values = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0])

print("Testing RBFInterpolator with nearly colinear points")
print("Points shape:", points.shape)
print("Values:", values)

try:
    rbf = interpolate.RBFInterpolator(points, values.reshape(-1, 1))
    result = rbf(points).flatten()
    
    print("\nRBF result:  ", result)
    print("Expected:    ", values)
    print("Difference:  ", result - values)
    print("Max abs diff:", np.max(np.abs(result - values)))
    
    if not np.allclose(result, values, rtol=1e-5, atol=1e-5):
        print("\n❌ BUG: RBFInterpolator doesn't pass through given points!")
        print("RBFInterpolator should interpolate exactly at training points")
    else:
        print("\n✅ No bug found")
except Exception as e:
    print(f"\n⚠️ Exception raised: {e}")