import scipy.signal as sig
import numpy as np

# Demonstrate the bug: Tukey(alpha=1) != Hann for small M with sym=False
M = 2
tukey = sig.windows.tukey(M, alpha=1.0, sym=False)
hann = sig.windows.hann(M, sym=False)

print(f"Tukey(M={M}, alpha=1, sym=False): {tukey}")
print(f"Hann(M={M}, sym=False): {hann}")
print(f"Documentation claims these should be equal, but they are not.")
print(f"Difference: {tukey - hann}")