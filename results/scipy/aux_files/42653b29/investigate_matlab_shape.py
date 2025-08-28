"""Investigate MATLAB shape handling."""

import scipy.io
import numpy as np
import tempfile
import os

# Test with a 1D array
data = {'A': np.array([0.0, 0.0])}

print("Original data:")
print(f"  A shape: {data['A'].shape}")
print(f"  A value: {data['A']}")

with tempfile.NamedTemporaryFile(suffix='.mat', delete=False) as f:
    filename = f.name

try:
    # Save and load
    scipy.io.savemat(filename, data)
    loaded = scipy.io.loadmat(filename)
    
    print("\nLoaded data:")
    print(f"  Keys: {[k for k in loaded.keys() if not k.startswith('__')]}")
    print(f"  A shape: {loaded['A'].shape}")
    print(f"  A value: {loaded['A']}")
    
    # Check if transposing fixes it
    print("\nTrying with squeeze=True option:")
    loaded2 = scipy.io.loadmat(filename, squeeze_me=True)
    print(f"  A shape: {loaded2['A'].shape}")
    print(f"  A value: {loaded2['A']}")
    
finally:
    if os.path.exists(filename):
        os.unlink(filename)