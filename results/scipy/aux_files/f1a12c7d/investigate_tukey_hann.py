import scipy.signal as sig
import numpy as np

print("Comparing Tukey(alpha=1) with Hann window for small M values:")

for M in range(1, 6):
    print(f"\nM = {M}:")
    tukey = sig.windows.tukey(M, alpha=1.0)
    hann = sig.windows.hann(M, sym=False)
    
    print(f"  Tukey(alpha=1): {tukey}")
    print(f"  Hann(sym=False): {hann}")
    print(f"  Match: {np.allclose(tukey, hann)}")
    
# Check documentation claim
print("\n\nChecking if documentation claims Tukey(alpha=1) = Hann...")
doc = sig.windows.tukey.__doc__
if doc and ('hann' in doc.lower() or 'hanning' in doc.lower()):
    print("Documentation mentions Hann/Hanning relationship")
    # Find the relevant section
    for line in doc.split('\n'):
        if 'hann' in line.lower():
            print(f"  -> {line.strip()}")