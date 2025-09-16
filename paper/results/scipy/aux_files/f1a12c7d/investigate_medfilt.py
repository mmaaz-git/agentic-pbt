import numpy as np
import scipy.signal as sig

# Test the failing case
x = [0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
kernel_size = 3

print("Original signal:", x)

filtered_once = sig.medfilt(x, kernel_size)
print("After first medfilt:", filtered_once)

filtered_twice = sig.medfilt(filtered_once, kernel_size)
print("After second medfilt:", filtered_twice)

filtered_thrice = sig.medfilt(filtered_twice, kernel_size)
print("After third medfilt:", filtered_thrice)

print("\nDifference between first and second:", filtered_once - filtered_twice)
print("Difference between second and third:", filtered_twice - filtered_thrice)

# This is expected behavior - median filter is not strictly idempotent
# It can take multiple applications to converge to a root signal