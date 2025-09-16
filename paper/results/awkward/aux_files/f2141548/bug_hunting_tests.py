#!/usr/bin/env python3
"""Bug hunting tests for awkward.typetracer - looking for edge cases and potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward.typetracer as tt
import awkward as ak

print("Bug hunting in awkward.typetracer module...")
print("=" * 60)

bugs_found = []

# Bug Hunt 1: Test view() with complex dtypes
print("\n1. Testing view() with complex dtypes edge cases...")
try:
    # Complex to float view
    array = tt.TypeTracerArray._new(np.dtype('complex128'), (4, 8))  # 16 bytes per element
    viewed = array.view(np.dtype('float64'))  # 8 bytes per element
    expected_shape = (4, 16)  # 8 * 16 / 8 = 16
    if viewed.shape != expected_shape:
        bugs_found.append(f"BUG: complex128 to float64 view: expected shape {expected_shape}, got {viewed.shape}")
    
    # Complex to int view
    array2 = tt.TypeTracerArray._new(np.dtype('complex64'), (3, 4))  # 8 bytes per element
    viewed2 = array2.view(np.dtype('int32'))  # 4 bytes per element
    expected_shape2 = (3, 8)  # 4 * 8 / 4 = 8
    if viewed2.shape != expected_shape2:
        bugs_found.append(f"BUG: complex64 to int32 view: expected shape {expected_shape2}, got {viewed2.shape}")
        
except Exception as e:
    bugs_found.append(f"BUG in view() with complex types: {e}")

# Bug Hunt 2: Test with zero-dimensional shapes
print("\n2. Testing with zero and empty shapes...")
try:
    # Empty shape (scalar)
    scalar = tt.TypeTracerArray._new(np.dtype('float64'), ())
    if scalar.size != 1:
        bugs_found.append(f"BUG: scalar size should be 1, got {scalar.size}")
    
    # Zero in shape
    try:
        zero_array = tt.TypeTracerArray._new(np.dtype('int32'), (0, 5))
        if zero_array.size != 0:
            bugs_found.append(f"BUG: array with 0 dimension should have size 0, got {zero_array.size}")
    except Exception as e:
        bugs_found.append(f"BUG: Cannot create array with 0 in shape: {e}")
        
except Exception as e:
    bugs_found.append(f"BUG with empty/zero shapes: {e}")

# Bug Hunt 3: Test view() with structured dtypes
print("\n3. Testing view() with structured dtypes...")
try:
    # Create a structured dtype
    struct_dtype = np.dtype([('x', 'f4'), ('y', 'f4')])  # 8 bytes total
    array = tt.TypeTracerArray._new(struct_dtype, (3, 4))
    
    # Try to view as float32 array
    try:
        viewed = array.view(np.dtype('float32'))
        expected_shape = (3, 8)  # 4 * 8 / 4 = 8
        if viewed.shape != expected_shape:
            bugs_found.append(f"BUG: structured to float32 view: expected {expected_shape}, got {viewed.shape}")
    except Exception as e:
        # This might legitimately fail
        pass
        
except Exception as e:
    # Structured dtypes might not be fully supported
    pass

# Bug Hunt 4: Test forget_length edge cases
print("\n4. Testing forget_length edge cases...")
try:
    # Scalar array
    scalar = tt.TypeTracerArray._new(np.dtype('int64'), ())
    forgotten_scalar = scalar.forget_length()
    if forgotten_scalar.shape != ():
        bugs_found.append(f"BUG: forget_length on scalar changed shape to {forgotten_scalar.shape}")
    
    # Already unknown length
    unknown_array = tt.TypeTracerArray._new(np.dtype('float32'), (tt.unknown_length, 10))
    forgotten_unknown = unknown_array.forget_length()
    if forgotten_unknown.shape != (tt.unknown_length, 10):
        bugs_found.append(f"BUG: forget_length on unknown length changed shape")
        
except Exception as e:
    bugs_found.append(f"BUG in forget_length edge cases: {e}")

# Bug Hunt 5: Test TypeTracerReport edge cases
print("\n5. Testing TypeTracerReport edge cases...")
try:
    report = tt.TypeTracerReport()
    
    # Test without setting labels
    array = tt.TypeTracerArray._new(np.dtype('float64'), (5,), form_key="test", report=report)
    try:
        array.touch_shape()
        array.touch_data()
        # Should this work without set_labels?
    except Exception as e:
        bugs_found.append(f"BUG: TypeTracerReport without set_labels: {e}")
    
    # Test with duplicate touches
    report2 = tt.TypeTracerReport()
    report2.set_labels(["key1", "key2"])
    array2 = tt.TypeTracerArray._new(np.dtype('int32'), (3,), form_key="key1", report=report2)
    
    array2.touch_data()
    array2.touch_data()  # Touch twice
    if report2.data_touched.count("key1") > 1:
        bugs_found.append("BUG: Duplicate touches counted multiple times")
        
except Exception as e:
    bugs_found.append(f"BUG in TypeTracerReport: {e}")

# Bug Hunt 6: Test extreme values
print("\n6. Testing with extreme values...")
try:
    # Very large shape
    try:
        large_array = tt.TypeTracerArray._new(np.dtype('uint8'), (2**30, 2**30))
        if large_array.nbytes < 0:  # Integer overflow?
            bugs_found.append(f"BUG: nbytes overflow with large shape: {large_array.nbytes}")
    except Exception as e:
        # Might legitimately fail with memory error
        pass
    
    # Negative dimensions (should fail)
    try:
        negative_array = tt.TypeTracerArray._new(np.dtype('float32'), (-1, 5))
        bugs_found.append("BUG: Should not allow negative dimensions in shape")
    except (TypeError, ValueError, AssertionError):
        pass  # Expected to fail
        
except Exception as e:
    bugs_found.append(f"BUG with extreme values: {e}")

# Bug Hunt 7: Test T property edge cases
print("\n7. Testing transpose (T) edge cases...")
try:
    # 0-d array
    scalar = tt.TypeTracerArray._new(np.dtype('float64'), ())
    transposed_scalar = scalar.T
    if transposed_scalar.shape != ():
        bugs_found.append(f"BUG: Transpose of scalar should be scalar, got shape {transposed_scalar.shape}")
    
    # 1-d array
    vector = tt.TypeTracerArray._new(np.dtype('int32'), (10,))
    transposed_vector = vector.T
    if transposed_vector.shape != (10,):
        bugs_found.append(f"BUG: Transpose of 1-d array should be unchanged, got {transposed_vector.shape}")
        
except Exception as e:
    bugs_found.append(f"BUG in transpose edge cases: {e}")

# Bug Hunt 8: Test getitem with unusual indices
print("\n8. Testing __getitem__ edge cases...")
try:
    array = tt.TypeTracerArray._new(np.dtype('float64'), (10, 20, 30))
    
    # Ellipsis
    try:
        sliced = array[...]
        if sliced.shape != (10, 20, 30):
            bugs_found.append(f"BUG: Ellipsis indexing changed shape to {sliced.shape}")
    except Exception as e:
        bugs_found.append(f"BUG: Ellipsis indexing failed: {e}")
    
    # newaxis
    try:
        expanded = array[np.newaxis, :, :, :]
        if expanded.shape != (1, 10, 20, 30):
            bugs_found.append(f"BUG: newaxis didn't add dimension correctly: {expanded.shape}")
    except Exception as e:
        bugs_found.append(f"BUG: newaxis indexing failed: {e}")
    
    # Multiple ellipsis (should fail)
    try:
        double_ellipsis = array[..., ...]
        bugs_found.append("BUG: Should not allow multiple ellipsis")
    except NotImplementedError:
        pass  # Expected
        
except Exception as e:
    bugs_found.append(f"BUG in getitem edge cases: {e}")

# Bug Hunt 9: Test unknown_length interactions
print("\n9. Testing unknown_length interactions...")
try:
    unknown_array = tt.TypeTracerArray._new(np.dtype('int64'), (tt.unknown_length, 5))
    
    # Size with unknown length
    size = unknown_array.size
    if size != tt.unknown_length and not isinstance(size, type(tt.unknown_length)):
        bugs_found.append(f"BUG: Size with unknown_length should propagate unknown, got {size}")
    
    # nbytes with unknown length
    nbytes = unknown_array.nbytes
    if nbytes != tt.unknown_length and not isinstance(nbytes, type(tt.unknown_length)):
        bugs_found.append(f"BUG: nbytes with unknown_length should propagate unknown, got {nbytes}")
        
except Exception as e:
    bugs_found.append(f"BUG with unknown_length: {e}")

# Bug Hunt 10: Test copy() method
print("\n10. Testing copy() method...")
try:
    original = tt.TypeTracerArray._new(np.dtype('float32'), (3, 4, 5))
    copied = original.copy()
    
    # Check if it's the same object (should it be?)
    if copied is not original:
        bugs_found.append("BUG: copy() should return self for TypeTracerArray")
    
    # Check properties are preserved
    if copied.shape != original.shape or copied.dtype != original.dtype:
        bugs_found.append("BUG: copy() changed shape or dtype")
        
except Exception as e:
    bugs_found.append(f"BUG in copy(): {e}")

# Print results
print("\n" + "=" * 60)
print("BUG HUNT RESULTS")
print("=" * 60)

if bugs_found:
    print(f"\n🐛 Found {len(bugs_found)} potential bug(s):\n")
    for i, bug in enumerate(bugs_found, 1):
        print(f"{i}. {bug}")
else:
    print("\n✅ No bugs found in the tested scenarios")

print("\n" + "=" * 60)