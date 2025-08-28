"""Additional edge case tests for pylong_join."""

from hypothesis import given, strategies as st, settings
from Cython.Utility import pylong_join
import sys


@given(st.integers(min_value=1000, max_value=10000))
@settings(max_examples=10)
def test_large_count_performance(count):
    """Test with very large count values - check for performance issues or crashes."""
    result = pylong_join(count)
    
    # Should still maintain properties even with large counts
    assert result.startswith('(')
    assert result.endswith(')')
    
    # Check parentheses balance
    assert result.count('(') == result.count(')')
    
    # The result should be quite long
    assert len(result) > count * 10  # rough estimate


@given(
    st.integers(min_value=1, max_value=10),
    st.text(min_size=0, max_size=0)  # empty string
)
def test_empty_digits_ptr(count, empty_ptr):
    """Test with empty string as digits_ptr."""
    try:
        result = pylong_join(count, empty_ptr)
        # Check if empty string is handled
        print(f"Empty digits_ptr result: {result[:100]}...")
        # Should have [0], [1], etc without prefix
        for i in range(count):
            assert f'[{i}]' in result
    except Exception as e:
        print(f"Empty digits_ptr raised: {e}")


@given(
    st.integers(min_value=1, max_value=10),
    st.text(min_size=0, max_size=0)  # empty string
)
def test_empty_join_type(count, empty_type):
    """Test with empty string as join_type."""
    try:
        result = pylong_join(count, 'digits', empty_type)
        # Check if empty type is handled
        print(f"Empty join_type result: {result[:100]}...")
        # Should have ()digits[n] pattern
        for i in range(count):
            assert f'()digits[{i}]' in result
    except Exception as e:
        print(f"Empty join_type raised: {e}")


@given(st.integers(min_value=1, max_value=10))
def test_special_chars_in_params(count):
    """Test with special characters in parameters."""
    # Test with characters that might break C code
    special_cases = [
        ('digits/*comment*/', 'unsigned long'),
        ('digits', 'unsigned/**/long'),
        ('dig"its', 'unsigned long'),  # quote in name
        ('digits\\n', 'unsigned long'),  # newline
        ('digits;', 'unsigned long'),  # semicolon
    ]
    
    for digits_ptr, join_type in special_cases:
        try:
            result = pylong_join(count, digits_ptr, join_type)
            # If it doesn't crash, the special chars are in the output
            assert digits_ptr in result or join_type in result
        except Exception:
            # Some special chars might reasonably cause exceptions
            pass


@given(st.floats())
def test_non_integer_count(count):
    """Test with non-integer count values."""
    try:
        result = pylong_join(count)
        # If it accepts floats, check behavior
        if count == int(count) and count >= 1:
            # Should work like the integer version
            assert '(unsigned long)' in result
    except (TypeError, ValueError) as e:
        # Expected for non-integer inputs
        pass
    except Exception as e:
        print(f"Unexpected exception for float count {count}: {e}")


@given(st.text())
def test_string_count(count_str):
    """Test with string count values."""
    try:
        result = pylong_join(count_str)
        # Should probably fail for non-numeric strings
        print(f"String count '{count_str}' produced: {result[:50]}...")
    except (TypeError, ValueError):
        # Expected for string inputs
        pass
    except Exception as e:
        print(f"Unexpected exception for string count: {e}")


def test_sys_maxsize():
    """Test with sys.maxsize as count."""
    try:
        # This will likely cause memory issues or take forever
        result = pylong_join(sys.maxsize)
        print(f"sys.maxsize worked?! Result length: {len(result)}")
    except MemoryError:
        # Expected
        pass
    except Exception as e:
        print(f"sys.maxsize raised: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # Run a quick check
    print("Testing edge cases...")
    
    # Test with count=0 explicitly
    try:
        result = pylong_join(0)
        print(f"count=0 result: '{result}'")
    except Exception as e:
        print(f"count=0 raised: {e}")
    
    # Test with negative count
    try:
        result = pylong_join(-1)
        print(f"count=-1 result: '{result}'")
    except Exception as e:
        print(f"count=-1 raised: {e}")
    
    # Test with None
    try:
        result = pylong_join(None)
        print(f"count=None result: '{result}'")
    except Exception as e:
        print(f"count=None raised: {e}")