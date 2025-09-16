import numpy as np
import scipy.signal as sig

# Test case 1: Pure imaginary zeros
print("Test 1: Two different pure imaginary zeros")
z_orig = [0.0625j, 0.02734375j]
p_orig = [0j]
k_orig = 1.0

print(f"Original zeros: {z_orig}")
print(f"Original poles: {p_orig}")
print(f"Original gain: {k_orig}")

b, a = sig.zpk2tf(z_orig, p_orig, k_orig)
print(f"\nTransfer function coefficients:")
print(f"b (numerator): {b}")
print(f"a (denominator): {a}")

z_recovered, p_recovered, k_recovered = sig.tf2zpk(b, a)
print(f"\nRecovered zeros: {z_recovered}")
print(f"Recovered poles: {p_recovered}")
print(f"Recovered gain: {k_recovered}")

print("\nComparison:")
print(f"Zeros match: {np.allclose(sorted(z_orig, key=lambda x: x.imag), sorted(z_recovered, key=lambda x: x.imag))}")
print(f"Difference in zeros: {sorted(z_recovered, key=lambda x: x.imag) - np.array(sorted(z_orig, key=lambda x: x.imag))}")

print("\n" + "="*60)

# Test case 2: Duplicate pure imaginary zeros
print("\nTest 2: Duplicate pure imaginary zeros")
z_orig2 = [0.5j, 0.5j]
p_orig2 = [0j]
k_orig2 = 1.0

print(f"Original zeros: {z_orig2}")
print(f"Original poles: {p_orig2}")
print(f"Original gain: {k_orig2}")

b2, a2 = sig.zpk2tf(z_orig2, p_orig2, k_orig2)
print(f"\nTransfer function coefficients:")
print(f"b (numerator): {b2}")
print(f"a (denominator): {a2}")

z_recovered2, p_recovered2, k_recovered2 = sig.tf2zpk(b2, a2)
print(f"\nRecovered zeros: {z_recovered2}")
print(f"Recovered poles: {p_recovered2}")
print(f"Recovered gain: {k_recovered2}")

print("\nComparison:")
print(f"Zeros match: {np.allclose(sorted(z_orig2, key=lambda x: x.imag), sorted(z_recovered2, key=lambda x: x.imag))}")
print(f"Difference in zeros: {sorted(z_recovered2, key=lambda x: x.imag) - np.array(sorted(z_orig2, key=lambda x: x.imag))}")