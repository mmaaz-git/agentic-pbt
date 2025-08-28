import numpy as np
from scipy import interpolate

# Minimal reproduction of CubicSpline C2 continuity bug
x = np.array([0., 1., 2., 3.])
y = np.array([0.0, 0.0, 0.0, 5001.0])

cs = interpolate.CubicSpline(x, y)

# Check second derivative continuity at interior knot x=1
knot = x[1]
eps = 1e-10

second_deriv = cs.derivative(2)
left = second_deriv(knot - eps)
right = second_deriv(knot + eps)

print("Testing CubicSpline C2 continuity at knot x =", knot)
print("Second derivative from left: ", left)
print("Second derivative from right:", right)
print("Difference:", right - left)
print("Relative difference:", abs(right - left) / max(abs(left), abs(right), 1e-10))

if not np.allclose(left, right, rtol=1e-6, atol=1e-6):
    print("\n❌ BUG: CubicSpline second derivative is not continuous!")
    print("CubicSpline claims to be C2 smooth but second derivative jumps at knot")
else:
    print("\n✅ No bug found")