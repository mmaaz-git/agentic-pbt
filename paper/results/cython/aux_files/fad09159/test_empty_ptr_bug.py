"""Test to verify the empty digits_ptr bug."""

from Cython.Utility import pylong_join


def test_empty_digits_ptr_bug():
    """Verify that empty digits_ptr generates invalid C code."""
    
    # Test with empty digits_ptr
    result = pylong_join(3, '', 'unsigned long')
    print(f"Generated code with empty digits_ptr:\n{result}")
    
    # This generates: (((((((unsigned long)[2]) << PyLong_SHIFT) | (unsigned long)[1]) << PyLong_SHIFT) | (unsigned long)[0]))
    # Which is invalid C code - you can't index nothing
    
    # Check that it contains bare array indexing
    assert '[0]' in result
    assert '[1]' in result
    assert '[2]' in result
    
    # Check that there's no array name before the brackets
    # In valid code, we'd have something like "digits[0]" or "arr[0]"
    # But with empty string, we get just "[0]"
    assert '(unsigned long)[0]' in result
    
    print("\nThis is INVALID C code!")
    print("Array indexing requires an array name.")
    print("'[0]' by itself is not valid C syntax.")
    
    # Compare with valid code
    valid_result = pylong_join(3, 'digits', 'unsigned long')
    print(f"\nValid code for comparison:\n{valid_result}")
    
    return True


def test_empty_join_type_bug():
    """Test with empty join_type."""
    
    result = pylong_join(2, 'digits', '')
    print(f"Generated code with empty join_type:\n{result}")
    
    # This generates: (((((()digits[1]) << PyLong_SHIFT) | ()digits[0]))
    # The empty parentheses () before digits is unusual but might be valid C
    
    # Check the pattern
    assert '()digits[0]' in result
    assert '()digits[1]' in result
    
    print("\nThis generates '()digits[0]' which is likely INVALID C code!")
    print("Empty cast '()' is not valid C syntax.")
    
    return True


if __name__ == "__main__":
    print("Testing empty digits_ptr bug...")
    test_empty_digits_ptr_bug()
    
    print("\n" + "="*60 + "\n")
    
    print("Testing empty join_type bug...")
    test_empty_join_type_bug()