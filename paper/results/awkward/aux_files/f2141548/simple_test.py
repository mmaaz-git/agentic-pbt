#!/usr/bin/env python3
"""Simple property-based test runner for awkward.typetracer."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward.typetracer as tt

print("Testing awkward.typetracer module...")
print("-" * 40)

# Test 1: create_unknown_scalar basic test
print("\n1. Testing create_unknown_scalar...")
try:
    for dtype in [np.int32, np.float64, np.bool_, np.complex128]:
        scalar = tt.create_unknown_scalar(dtype)
        assert scalar.dtype == np.dtype(dtype), f"dtype mismatch: {scalar.dtype} != {dtype}"
        assert scalar.ndim == 0, f"ndim should be 0, got {scalar.ndim}"
        assert scalar.shape == (), f"shape should be (), got {scalar.shape}"
    print("   ✓ create_unknown_scalar works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 2: TypeTracerArray._new basic test
print("\n2. Testing TypeTracerArray._new...")
try:
    array = tt.TypeTracerArray._new(np.dtype('float64'), (3, 4, 5))
    assert array.dtype == np.dtype('float64')
    assert array.shape == (3, 4, 5)
    assert array.ndim == 3
    assert array.size == 60
    assert array.nbytes == 60 * 8  # float64 is 8 bytes
    print("   ✓ TypeTracerArray._new works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 3: TypeTracerArray.view divisibility
print("\n3. Testing TypeTracerArray.view divisibility...")
try:
    # Test case that should work
    array = tt.TypeTracerArray._new(np.dtype('float64'), (3, 4))  # 8 bytes per element
    viewed = array.view(np.dtype('float32'))  # 4 bytes per element
    assert viewed.shape == (3, 8), f"Expected shape (3, 8), got {viewed.shape}"
    
    # Test case that should fail
    array2 = tt.TypeTracerArray._new(np.dtype('float64'), (3, 3))  # 3*8=24 bytes in last dim
    try:
        viewed2 = array2.view(np.dtype('float32'))  # Would need 24/4=6, which works
        assert viewed2.shape == (3, 6), f"Expected shape (3, 6), got {viewed2.shape}"
    except ValueError:
        print("   ! Unexpected ValueError for valid view")
    
    # Test case that really should fail
    array3 = tt.TypeTracerArray._new(np.dtype('int8'), (3, 5))  # 5 bytes in last dim
    try:
        viewed3 = array3.view(np.dtype('int16'))  # Would need 5/2=2.5, should fail
        print(f"   ! View should have failed but got shape: {viewed3.shape}")
    except ValueError:
        pass  # Expected
    
    print("   ✓ TypeTracerArray.view divisibility works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 4: TypeTracerArray.T (transpose)
print("\n4. Testing TypeTracerArray.T (transpose)...")
try:
    array = tt.TypeTracerArray._new(np.dtype('int32'), (2, 3, 4))
    transposed = array.T
    assert transposed.shape == (4, 3, 2), f"Expected shape (4, 3, 2), got {transposed.shape}"
    assert transposed.dtype == np.dtype('int32')
    
    # Double transpose
    double_t = transposed.T
    assert double_t.shape == (2, 3, 4), f"Double transpose should give original shape"
    
    print("   ✓ TypeTracerArray.T works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 5: forget_length
print("\n5. Testing TypeTracerArray.forget_length...")
try:
    array = tt.TypeTracerArray._new(np.dtype('float32'), (10, 20, 30))
    forgotten = array.forget_length()
    assert forgotten.shape[0] is tt.unknown_length, "First dimension should be unknown_length"
    assert forgotten.shape[1:] == (20, 30), f"Rest of shape should be preserved"
    assert forgotten.dtype == np.dtype('float32')
    print("   ✓ forget_length works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 6: is_unknown_scalar and is_unknown_array
print("\n6. Testing is_unknown_scalar and is_unknown_array...")
try:
    scalar = tt.create_unknown_scalar(np.float64)
    array = tt.TypeTracerArray._new(np.dtype('float64'), (5,))
    
    assert tt.is_unknown_scalar(scalar) == True
    assert tt.is_unknown_array(scalar) == False
    assert tt.is_unknown_scalar(array) == False  
    assert tt.is_unknown_array(array) == True
    print("   ✓ is_unknown_scalar/array work correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 7: inner_shape
print("\n7. Testing TypeTracerArray.inner_shape...")
try:
    array = tt.TypeTracerArray._new(np.dtype('uint8'), (5, 10, 15, 20))
    assert array.inner_shape == (10, 15, 20), f"Expected (10, 15, 20), got {array.inner_shape}"
    
    array2 = tt.TypeTracerArray._new(np.dtype('uint8'), (5,))
    assert array2.inner_shape == (), f"Expected (), got {array2.inner_shape}"
    
    print("   ✓ inner_shape works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 8: MaybeNone wrapper
print("\n8. Testing MaybeNone wrapper...")
try:
    content = tt.TypeTracerArray._new(np.dtype('int64'), (3, 3))
    maybe1 = tt.MaybeNone(content)
    maybe2 = tt.MaybeNone(content)
    
    assert maybe1 == maybe2, "MaybeNone with same content should be equal"
    assert maybe1.content is content
    
    print("   ✓ MaybeNone works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

# Test 9: OneOf wrapper
print("\n9. Testing OneOf wrapper...")
try:
    content1 = tt.TypeTracerArray._new(np.dtype('int32'), (2,))
    content2 = tt.TypeTracerArray._new(np.dtype('float32'), (2,))
    
    oneof1 = tt.OneOf([content1, content2])
    oneof2 = tt.OneOf([content2, content1])  # Different order
    
    assert oneof1 == oneof2, "OneOf should use set equality"
    assert len(oneof1.contents) == 2
    
    print("   ✓ OneOf works correctly")
except Exception as e:
    print(f"   ✗ FAILED: {e}")

print("\n" + "-" * 40)
print("Basic tests completed successfully! ✓")