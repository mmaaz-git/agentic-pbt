import numpy as np
import scipy.signal as sig
import math

# Test the specific failing cases from the test
test_cases = [
    ([0.0625j, 0.02734375j], [0j], 1.0),
    ([0.5j, 0.5j], [0j], 1.0),
    ([], [0.0625j, 0.02734375j], 1.0),
    ([], [0.5j, 0.5j], 1.0)
]

for i, (z_orig, p_orig, k_orig) in enumerate(test_cases, 1):
    print(f"Test case {i}:")
    print(f"  Original: z={z_orig}, p={p_orig}, k={k_orig}")
    
    b, a = sig.zpk2tf(z_orig, p_orig, k_orig)
    z_rec, p_rec, k_rec = sig.tf2zpk(b, a)
    
    print(f"  Recovered: z={z_rec}, p={p_rec}, k={k_rec}")
    
    # Check with more reasonable tolerances
    if z_orig:
        z_match = np.allclose(sorted(z_orig, key=lambda x: (x.real, x.imag)), 
                               sorted(z_rec, key=lambda x: (x.real, x.imag)),
                               rtol=1e-7, atol=1e-9)
        print(f"  Zeros match (rtol=1e-7, atol=1e-9): {z_match}")
    
    if p_orig:
        p_match = np.allclose(sorted(p_orig, key=lambda x: (x.real, x.imag)),
                               sorted(p_rec, key=lambda x: (x.real, x.imag)),
                               rtol=1e-7, atol=1e-9)
        print(f"  Poles match (rtol=1e-7, atol=1e-9): {p_match}")
    
    # Check if the transfer functions are actually equivalent
    # by evaluating them at several points
    test_points = [1j, 2j, -1j, 1+1j, 2+3j]
    
    max_error = 0
    for s in test_points:
        # Evaluate original zpk
        num_orig = k_orig * np.prod([s - z for z in z_orig]) if z_orig else k_orig
        den_orig = np.prod([s - p for p in p_orig]) if p_orig else 1
        h_orig = num_orig / den_orig if den_orig != 0 else float('inf')
        
        # Evaluate recovered zpk  
        num_rec = k_rec * np.prod([s - z for z in z_rec]) if len(z_rec) > 0 else k_rec
        den_rec = np.prod([s - p for p in p_rec]) if len(p_rec) > 0 else 1
        h_rec = num_rec / den_rec if den_rec != 0 else float('inf')
        
        error = abs(h_orig - h_rec) if h_orig != float('inf') else 0
        max_error = max(max_error, error)
    
    print(f"  Max error in transfer function evaluation: {max_error}")
    print()