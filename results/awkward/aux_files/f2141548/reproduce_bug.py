#!/usr/bin/env python3
"""Attempt to reproduce specific bugs in awkward.typetracer."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward.typetracer as tt

print("Attempting to reproduce bugs in awkward.typetracer...")
print("=" * 60)

# Bug candidate 1: TypeTracerArray.copy() behavior
print("\nBug Candidate 1: TypeTracerArray.copy() returns self")
print("-" * 40)
try:
    original = tt.TypeTracerArray._new(np.dtype('float64'), (3, 4))
    copied = original.copy()
    
    print(f"original is copied: {original is copied}")
    print(f"original id: {id(original)}")
    print(f"copied id: {id(copied)}")
    
    # According to the code, copy() just calls touch_data() and returns self
    # This might be unexpected behavior - usually copy() creates a new object
    if original is copied:
        print("✓ Confirmed: copy() returns the same object (self)")
        print("  This violates the normal expectation that copy() creates a new object")
except Exception as e:
    print(f"Error: {e}")

# Bug candidate 2: forget_length on scalar
print("\nBug Candidate 2: forget_length() on scalar array")
print("-" * 40)
try:
    scalar = tt.TypeTracerArray._new(np.dtype('int32'), ())
    print(f"Original scalar shape: {scalar.shape}")
    
    forgotten = scalar.forget_length()
    print(f"After forget_length shape: {forgotten.shape}")
    
    # forget_length should only affect arrays with at least 1 dimension
    # But it blindly does (unknown_length, *shape[1:]) which for scalar gives (unknown_length,)
    if len(forgotten.shape) > 0:
        print("✓ Confirmed BUG: forget_length() on scalar creates 1-d array!")
        print(f"  Expected shape (), got {forgotten.shape}")
except Exception as e:
    print(f"Error: {e}")

# Bug candidate 3: TypeTracerReport without labels
print("\nBug Candidate 3: TypeTracerReport behavior without set_labels")
print("-" * 40)
try:
    report = tt.TypeTracerReport()
    array = tt.TypeTracerArray._new(np.dtype('float64'), (5,), form_key="test_key", report=report)
    
    # Try to touch without setting labels first
    try:
        array.touch_shape()
        print("touch_shape succeeded without set_labels")
        print(f"shape_touched: {report.shape_touched}")
    except AttributeError as e:
        print(f"✓ Confirmed BUG: AttributeError when touching without set_labels: {e}")
    except Exception as e:
        print(f"Other error: {e}")
        
except Exception as e:
    print(f"Error: {e}")

# Bug candidate 4: View with remainder calculation
print("\nBug Candidate 4: view() remainder calculation with unknown_length")
print("-" * 40)
try:
    # Create array with unknown_length in shape
    array = tt.TypeTracerArray._new(np.dtype('float64'), (tt.unknown_length, 3))
    print(f"Original shape: {array.shape}, dtype: {array.dtype}")
    
    # Try to view as float32
    viewed = array.view(np.dtype('float32'))
    print(f"Viewed shape: {viewed.shape}, dtype: {viewed.dtype}")
    
    # The calculation: 3 * 8 / 4 = 6, should work
    if viewed.shape[-1] != 6:
        print(f"Unexpected shape after view: {viewed.shape}")
    
    # Now try with a case that shouldn't divide evenly
    array2 = tt.TypeTracerArray._new(np.dtype('float64'), (5, 3))
    try:
        viewed2 = array2.view(np.dtype('int8'))  # 3*8=24 bytes, divides by 1
        print(f"View succeeded: {viewed2.shape}")
    except ValueError:
        print("View correctly failed for non-divisible case")
        
except Exception as e:
    print(f"Error: {e}")

# Bug candidate 5: Extreme shape values
print("\nBug Candidate 5: Integer overflow in size/nbytes calculation")
print("-" * 40)
try:
    # Create array with very large dimensions
    large_dim = 2**31  # Near int32 max
    array = tt.TypeTracerArray._new(np.dtype('int64'), (large_dim, large_dim))
    
    size = array.size
    nbytes = array.nbytes
    
    print(f"Shape: {array.shape}")
    print(f"Size: {size} (type: {type(size).__name__})")
    print(f"Nbytes: {nbytes} (type: {type(nbytes).__name__})")
    
    # Check for overflow
    expected_size = large_dim * large_dim
    if size != expected_size:
        print(f"✓ Possible overflow: expected {expected_size}, got {size}")
        
except Exception as e:
    print(f"Error creating large array: {e}")

print("\n" + "=" * 60)
print("Bug reproduction attempts completed.")
print("Most likely bug: forget_length() on scalar arrays changes dimensionality!")