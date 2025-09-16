import scipy.signal as sig
import numpy as np

print("Comparing Tukey(alpha=1) with Hann window for larger M values:")

for M in [10, 20, 50, 100]:
    tukey = sig.windows.tukey(M, alpha=1.0, sym=False)
    hann = sig.windows.hann(M, sym=False)
    
    # Check if they match
    match = np.allclose(tukey, hann, rtol=1e-10, atol=1e-12)
    
    # Calculate max difference
    max_diff = np.max(np.abs(tukey - hann))
    
    print(f"\nM = {M}:")
    print(f"  Match: {match}")
    print(f"  Max difference: {max_diff}")
    
    if M <= 20:
        print(f"  First 5 values Tukey: {tukey[:5]}")
        print(f"  First 5 values Hann:  {hann[:5]}")

# Let's also check with sym=True (default)
print("\n\nWith sym=True (default):")
for M in [2, 3, 4, 5, 10]:
    tukey = sig.windows.tukey(M, alpha=1.0)  # default sym=True
    hann = sig.windows.hann(M)  # default sym=True
    
    match = np.allclose(tukey, hann, rtol=1e-10, atol=1e-12)
    max_diff = np.max(np.abs(tukey - hann))
    
    print(f"\nM = {M}:")
    print(f"  Tukey: {tukey}")
    print(f"  Hann:  {hann}")
    print(f"  Match: {match}, Max diff: {max_diff}")