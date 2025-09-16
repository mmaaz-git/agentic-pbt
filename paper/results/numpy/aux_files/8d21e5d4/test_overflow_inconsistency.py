"""
Property-based test that discovers overflow handling inconsistency in NumPy
"""
import numpy as np
from hypothesis import given, strategies as st


@given(
    st.sampled_from([np.int8, np.uint8, np.int16, np.uint16, np.int32, np.uint32]),
    st.integers()
)
def test_integer_dtype_overflow_consistency(dtype, value):
    """Test that integer dtype overflow handling is consistent across operations"""
    info = np.iinfo(dtype)
    
    # Only test values outside the valid range
    if info.min <= value <= info.max:
        return  # Skip values within range
    
    # Test 1: Creating array directly with out-of-bounds value
    try:
        arr1 = np.array([value], dtype=dtype)
        created_directly = True
        direct_value = arr1[0]
    except OverflowError:
        created_directly = False
        direct_value = None
    
    # Test 2: Creating via astype
    arr_big = np.array([value], dtype=np.int64)
    arr2 = arr_big.astype(dtype)
    astype_value = arr2[0]
    
    # Test 3: Getting there via arithmetic
    if value > info.max:
        # Start at max and add difference
        diff = value - info.max
        arr3 = np.array([info.max], dtype=dtype)
        # Add the difference in chunks to avoid Python int overflow checks
        while diff > 0:
            chunk = min(diff, info.max)
            arr3 = arr3 + chunk
            diff -= chunk
        arithmetic_value = arr3[0]
    else:
        # value < info.min
        diff = info.min - value
        arr3 = np.array([info.min], dtype=dtype)
        while diff > 0:
            chunk = min(diff, abs(info.min))
            arr3 = arr3 - chunk
            diff -= chunk
        arithmetic_value = arr3[0]
    
    # Property: All methods should give same result
    # But they don't!
    
    # astype and arithmetic both wrap
    assert astype_value == arithmetic_value, \
        f"astype and arithmetic give different results for {value} in {dtype.__name__}"
    
    # But direct creation raises OverflowError
    assert not created_directly, \
        f"Expected OverflowError when creating {dtype.__name__} with value {value}, but it succeeded with {direct_value}"


def demonstrate_bug():
    """Demonstrate the inconsistency as a concrete bug"""
    print("NUMPY INTEGER OVERFLOW INCONSISTENCY BUG")
    print("="*50)
    
    dtype = np.uint8
    value = 256
    
    print(f"\nTrying to store value {value} in {dtype.__name__}:")
    print("-" * 40)
    
    # Method 1: Direct array creation
    print("\nMethod 1: np.array([256], dtype=uint8)")
    try:
        arr = np.array([value], dtype=dtype)
        print(f"  Result: {arr[0]}")
    except OverflowError as e:
        print(f"  OverflowError: {e}")
    
    # Method 2: Using astype
    print("\nMethod 2: np.array([256]).astype(uint8)")
    arr = np.array([value]).astype(dtype)
    print(f"  Result: {arr[0]}")
    
    # Method 3: Arithmetic
    print("\nMethod 3: np.array([255], dtype=uint8) + 1")
    arr = np.array([255], dtype=dtype) + 1
    print(f"  Result: {arr[0]}")
    
    print("\n" + "="*50)
    print("BUG: Same value, different behavior!")
    print("- Direct creation: Raises OverflowError")
    print("- astype(): Silently wraps to 0")
    print("- Arithmetic: Silently wraps to 0")
    print("\nThis inconsistency can lead to:")
    print("1. Unexpected errors when refactoring code")
    print("2. Silent data corruption vs explicit errors")
    print("3. Confusion about NumPy's overflow policy")
    
    return True


if __name__ == "__main__":
    demonstrate_bug()
    
    # Run the property test
    print("\n" + "="*50)
    print("Running property-based test...")
    print("="*50)
    
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-q", "-k", "test_integer_dtype_overflow_consistency"])