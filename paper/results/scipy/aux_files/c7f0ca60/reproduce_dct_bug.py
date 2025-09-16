import numpy as np
import scipy.fft

x = np.array([1.0])
print(f"Input: {x}")

print("\nTesting type 1 transforms with single-element array:")
print("-" * 50)

try:
    result = scipy.fft.dct(x, type=1)
    print(f"DCT type 1: {result}")
except RuntimeError as e:
    print(f"DCT type 1: RuntimeError - {e}")

try:
    result = scipy.fft.idct(x, type=1)
    print(f"IDCT type 1: {result}")
except RuntimeError as e:
    print(f"IDCT type 1: RuntimeError - {e}")

try:
    result = scipy.fft.dst(x, type=1)
    print(f"DST type 1: {result}")
except RuntimeError as e:
    print(f"DST type 1: RuntimeError - {e}")

try:
    result = scipy.fft.idst(x, type=1)
    print(f"IDST type 1: {result}")
except RuntimeError as e:
    print(f"IDST type 1: RuntimeError - {e}")

print("\nTypes 2-4 all work correctly:")
print("-" * 50)
for t in [2, 3, 4]:
    print(f"DCT type {t}: {scipy.fft.dct(x, type=t)}")
    print(f"IDCT type {t}: {scipy.fft.idct(x, type=t)}")