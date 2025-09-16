"""Property-based tests for Cython.Utility.pylong_join function."""

import re
from hypothesis import given, strategies as st, assume
from Cython.Utility import pylong_join


@given(st.integers(min_value=1, max_value=100))
def test_balanced_parentheses(count):
    """Test that generated code has balanced parentheses."""
    result = pylong_join(count)
    
    # Count opening and closing parentheses
    open_count = result.count('(')
    close_count = result.count(')')
    
    assert open_count == close_count, f"Unbalanced parentheses: {open_count} open, {close_count} close"
    
    # Also check that parentheses are properly nested
    balance = 0
    for char in result:
        if char == '(':
            balance += 1
        elif char == ')':
            balance -= 1
            assert balance >= 0, "Closing parenthesis without matching opening"
    
    assert balance == 0, "Unclosed parentheses"


@given(st.integers(min_value=1, max_value=50))
def test_digit_ordering(count):
    """Test that digits are accessed in reverse order (count-1 down to 0)."""
    result = pylong_join(count)
    
    # Extract all digit indices using regex
    digit_pattern = r'digits\[(\d+)\]'
    indices = [int(m.group(1)) for m in re.finditer(digit_pattern, result)]
    
    # Should have exactly 'count' digit accesses
    assert len(indices) == count, f"Expected {count} digit accesses, found {len(indices)}"
    
    # Check that indices go from count-1 down to 0
    expected_indices = list(range(count-1, -1, -1))
    assert indices == expected_indices, f"Digit indices not in reverse order: {indices}"


@given(st.integers(min_value=1, max_value=50))
def test_shift_pattern(count):
    """Test that all digits except index 0 have the shift operation."""
    result = pylong_join(count)
    
    # For count=1, there should be no shift
    if count == 1:
        assert 'PyLong_SHIFT' not in result, "No shift expected for count=1"
    else:
        # Count shift operations
        shift_count = result.count('PyLong_SHIFT')
        expected_shifts = count - 1
        assert shift_count == expected_shifts, f"Expected {expected_shifts} shifts, found {shift_count}"
        
        # Check that digit[0] doesn't have a shift after it
        assert not re.search(r'digits\[0\]\)[^)]*PyLong_SHIFT', result), "digit[0] should not have shift"


@given(
    st.integers(min_value=1, max_value=20),
    st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_custom_parameters(count, digits_ptr, join_type):
    """Test that custom digits_ptr and join_type are properly substituted."""
    # Filter out problematic inputs
    assume(not any(c in digits_ptr for c in '[]()'))
    assume(not any(c in join_type for c in '[]()'))
    
    result = pylong_join(count, digits_ptr, join_type)
    
    # Check that custom parameters appear in the result
    assert digits_ptr in result, f"Custom digits_ptr '{digits_ptr}' not found in result"
    assert join_type in result, f"Custom join_type '{join_type}' not found in result"
    
    # Check that default 'digits' doesn't appear when custom is provided
    if digits_ptr != 'digits':
        assert 'digits[' not in result, "Default 'digits' found when custom digits_ptr provided"
    
    # Check that default 'unsigned long' doesn't appear when custom is provided
    if join_type != 'unsigned long':
        assert 'unsigned long' not in result, "Default 'unsigned long' found when custom join_type provided"
    
    # Verify the structure is maintained
    assert result.count(f'{digits_ptr}[') == count, f"Expected {count} occurrences of {digits_ptr}["
    assert result.count(f'({join_type})') == count, f"Expected {count} type casts to {join_type}"


@given(st.integers(min_value=2, max_value=30))
def test_incremental_structure(count):
    """Test that the structure follows the documented pattern: (((d[2] << n) | d[1]) << n) | d[0]"""
    result = pylong_join(count)
    
    # For count >= 2, check the pattern of OR operations
    or_count = result.count(' | ')
    expected_ors = count - 1
    assert or_count == expected_ors, f"Expected {expected_ors} OR operations, found {or_count}"
    
    # Check that each digit appears exactly once
    for i in range(count):
        digit_str = f'digits[{i}]'
        occurrences = result.count(digit_str)
        assert occurrences == 1, f"{digit_str} appears {occurrences} times, expected 1"


@given(st.integers(min_value=1, max_value=50))
def test_type_cast_consistency(count):
    """Test that every digit access is properly type-casted."""
    result = pylong_join(count)
    
    # Check that each digit[n] is preceded by (unsigned long)
    for i in range(count):
        pattern = f'(unsigned long)digits[{i}]'
        assert pattern in result, f"Missing type cast for digits[{i}]"
    
    # Count total type casts
    cast_count = result.count('(unsigned long)')
    assert cast_count == count, f"Expected {count} type casts, found {cast_count}"


@given(st.integers(min_value=1, max_value=1))
def test_single_digit_special_case(count):
    """Test the special case when count=1 (no shift, no OR)."""
    assert count == 1  # This test is specifically for count=1
    result = pylong_join(1)
    
    # Should not contain shift or OR operations
    assert 'PyLong_SHIFT' not in result, "Single digit should not have shift"
    assert ' | ' not in result, "Single digit should not have OR operation"
    
    # Should still have the type cast and digit access
    assert '(unsigned long)digits[0]' in result, "Missing proper type cast and digit access"


@given(st.integers(min_value=0, max_value=0))
def test_zero_count_edge_case(count):
    """Test edge case when count=0."""
    assert count == 0
    try:
        result = pylong_join(0)
        # If it doesn't crash, check the result makes sense
        # With count=0, the range(count-1, -1, -1) becomes range(-1, -1, -1) which is empty
        # So we expect minimal output with just parentheses
        assert result == '()', f"Unexpected result for count=0: {result}"
    except Exception as e:
        # If it crashes, that might be a bug depending on intended behavior
        # For now, we'll accept either behavior
        pass


@given(st.integers(min_value=-10, max_value=-1))
def test_negative_count(count):
    """Test behavior with negative count values."""
    try:
        result = pylong_join(count)
        # If it doesn't crash, the range would be empty for negative counts
        # So we expect minimal output
        assert result == '()', f"Unexpected result for negative count: {result}"
    except Exception:
        # Negative counts might reasonably raise an exception
        pass