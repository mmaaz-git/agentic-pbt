import numpy as np

print("Testing numpy.fft.irfftn bug with 1-element arrays")
print("=" * 60)

# Test 1: Single element real array
x = np.array([1.0])
print(f"\nOriginal array: {x}")
print(f"Shape: {x.shape}")

# Forward transform
rfft_result = np.fft.rfftn(x)
print(f"After rfftn: {rfft_result}")
print(f"Shape after rfftn: {rfft_result.shape}")

# Inverse transform - this should give back the original array
print("\nAttempting inverse transform with irfftn...")
try:
    irfft_result = np.fft.irfftn(rfft_result)
    print(f"After irfftn: {irfft_result}")
    print(f"Shapes match: {irfft_result.shape == x.shape}")
    print(f"Values match: {np.allclose(irfft_result, x)}")
except ValueError as e:
    print(f"ERROR: {e}")
    print("BUG: irfftn fails on 1-element arrays from rfftn!")

# Test 2: Verify the same issue occurs with irfft2
print("\n" + "=" * 60)
print("Testing with 2D functions...")

x_2d = np.array([[1.0]])
print(f"\nOriginal 2D array: {x_2d}")
print(f"Shape: {x_2d.shape}")

rfft2_result = np.fft.rfft2(x_2d)
print(f"After rfft2: {rfft2_result}")
print(f"Shape after rfft2: {rfft2_result.shape}")

print("\nAttempting inverse transform with irfft2...")
try:
    irfft2_result = np.fft.irfft2(rfft2_result)
    print(f"After irfft2: {irfft2_result}")
except ValueError as e:
    print(f"ERROR: {e}")
    print("BUG: irfft2 also fails on 1x1 arrays!")

# Test 3: Show that it works fine with 2+ elements
print("\n" + "=" * 60)
print("For comparison, 2-element array works fine:")

x2 = np.array([1.0, 2.0])
print(f"\nOriginal array: {x2}")
rfft_x2 = np.fft.rfftn(x2)
print(f"After rfftn: {rfft_x2}")
irfft_x2 = np.fft.irfftn(rfft_x2)
print(f"After irfftn: {irfft_x2}")
print(f"Round-trip successful: {np.allclose(x2, irfft_x2)}")