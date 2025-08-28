import numpy as np
import numpy.dtypes
from hypothesis import given, strategies as st


@given(st.integers(0, 255), st.integers(0, 1000))
def test_uint8_addition_inconsistency(base_value, add_value):
    """Test inconsistency in uint8 overflow handling"""
    dt = np.dtype('uint8')
    
    # Create base array
    arr = np.array([base_value], dtype=dt)
    
    # Method 1: Add as Python integer (works, wraps silently)
    result1 = arr + add_value
    
    # Method 2: Create array with sum value
    sum_value = base_value + add_value
    
    if sum_value <= 255:
        # Should work fine
        arr2 = np.array([sum_value], dtype=dt)
        assert arr2[0] == result1[0]
    else:
        # This will raise OverflowError
        try:
            arr2 = np.array([sum_value], dtype=dt)
            # If we get here, it should match the wrapped value
            assert arr2[0] == result1[0]
        except OverflowError:
            # But arithmetic gives wrapped result without error
            expected_wrapped = sum_value % 256
            assert result1[0] == expected_wrapped
            # This is the inconsistency!
            print(f"INCONSISTENCY: arr + {add_value} = {result1[0]} (wraps), but np.array([{sum_value}], dtype=uint8) raises OverflowError")
            return False  # Signal we found the issue
    
    return True


# Simpler demonstration
def demonstrate_inconsistency():
    """Demonstrate the inconsistency directly"""
    print("Demonstrating uint8 overflow inconsistency:\n")
    
    # Creating array with out-of-bounds value
    print("1. Creating array with value 256 (out of uint8 range):")
    try:
        arr = np.array([256], dtype=np.uint8)
        print(f"   Result: {arr[0]}")
    except OverflowError as e:
        print(f"   OverflowError: {e}")
    
    print("\n2. Adding 1 to 255 in uint8 array:")
    arr = np.array([255], dtype=np.uint8)
    result = arr + 1
    print(f"   Result: {result[0]} (wraps silently)")
    
    print("\n3. Creating uint8 array, then adding values that overflow:")
    arr = np.array([200], dtype=np.uint8)
    result = arr + 100  # 200 + 100 = 300, which is > 255
    print(f"   200 + 100 = {result[0]} (wraps to {300 % 256})")
    
    print("\n4. But creating array directly with 300:")
    try:
        arr = np.array([300], dtype=np.uint8)
        print(f"   Result: {arr[0]}")
    except OverflowError as e:
        print(f"   OverflowError: {e}")
    
    print("\nThis is inconsistent behavior - arithmetic wraps silently,")
    print("but array creation with out-of-bounds values raises an error.")
    
    # More tests
    print("\n5. Testing with negative values:")
    print("   Subtracting 1 from 0 in uint8:")
    arr = np.array([0], dtype=np.uint8)
    result = arr - 1
    print(f"   Result: {result[0]} (wraps to 255)")
    
    print("\n   Creating array with -1:")
    try:
        arr = np.array([-1], dtype=np.uint8)
        print(f"   Result: {arr[0]}")
    except OverflowError as e:
        print(f"   OverflowError: {e}")


# Test integer dtype consistency across different sizes
@given(st.sampled_from([np.int8, np.int16, np.int32, np.uint8, np.uint16, np.uint32]))
def test_integer_overflow_consistency(dtype):
    """Test if all integer dtypes have same overflow inconsistency"""
    info = np.iinfo(dtype)
    max_val = info.max
    
    # Create array at max value
    arr = np.array([max_val], dtype=dtype)
    
    # Add 1 (should wrap)
    result = arr + 1
    expected_wrap = info.min if np.issubdtype(dtype, np.signedinteger) else 0
    assert result[0] == expected_wrap, f"Wraparound failed for {dtype}"
    
    # But creating with max+1 should fail
    try:
        arr2 = np.array([max_val + 1], dtype=dtype)
        # If it doesn't fail, that's also interesting
        print(f"WARNING: {dtype} accepted {max_val + 1} without error, got {arr2[0]}")
    except OverflowError:
        # Expected for consistency with uint8
        pass
    
    # Test the other boundary too
    min_val = info.min
    arr = np.array([min_val], dtype=dtype)
    result = arr - 1
    expected_wrap = info.max
    assert result[0] == expected_wrap, f"Underflow wrap failed for {dtype}"
    
    # Creating with min-1 should also fail
    try:
        arr2 = np.array([min_val - 1], dtype=dtype)
        print(f"WARNING: {dtype} accepted {min_val - 1} without error, got {arr2[0]}")
    except OverflowError:
        pass


if __name__ == "__main__":
    import sys
    
    # First demonstrate the issue clearly
    demonstrate_inconsistency()
    
    # Then run hypothesis tests
    print("\n" + "="*60)
    print("Running property-based tests...")
    print("="*60)
    
    import pytest
    # Run pytest on this file
    sys.exit(pytest.main([__file__, "-v", "--tb=short", "-q"]))