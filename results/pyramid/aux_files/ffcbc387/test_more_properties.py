#!/usr/bin/env python3
"""Additional property tests to find edge cases."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
from pyramid import encode, settings as pyramid_settings, util

# Test: urlencode should handle bytes values
@given(
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(
            st.binary(),
            st.text()
        )
    )
)
def test_urlencode_with_bytes(data):
    """Test that urlencode handles bytes values correctly."""
    try:
        result = encode.urlencode(data)
        # If it succeeds, check that result is a string
        assert isinstance(result, str)
    except (TypeError, AttributeError) as e:
        # This might be expected for bytes
        pass

# Test: Look for issues with special characters in keys
@given(
    st.dictionaries(
        st.text(min_size=1).map(lambda x: f"={x}="),  # Keys with = signs
        st.text()
    )
)
def test_urlencode_equals_in_keys(data):
    """Test urlencode with = signs in keys."""
    result = encode.urlencode(data)
    # Parse it back manually to check correctness
    # The = signs in keys should be encoded as %3D
    for key in data:
        encoded_key = encode.quote_plus(key)
        assert '%3D' in encoded_key or '=' not in key

# Test: Check behavior with empty strings vs None
def test_urlencode_empty_vs_none_detailed():
    """Detailed comparison of empty string vs None handling."""
    # According to the docstring, None values are dropped (v1.5 change)
    # But looking at the code, None produces "key=" without a value
    
    data_none = {'a': None, 'b': 'test'}
    data_empty = {'a': '', 'b': 'test'}
    
    result_none = encode.urlencode(data_none)
    result_empty = encode.urlencode(data_empty)
    
    print(f"None value result: {result_none}")
    print(f"Empty string result: {result_empty}")
    
    # These should be the same based on the implementation
    assert result_none == result_empty

# Test: Check if the docstring claim about None being "dropped" is accurate
def test_urlencode_none_not_dropped():
    """Test that None values are NOT actually dropped as docstring claims."""
    data = {'key': None}
    result = encode.urlencode(data)
    
    # Docstring says "dropped" but code shows it produces "key="
    print(f"Result for {{'key': None}}: {result!r}")
    
    # If truly dropped, result would be empty
    # But implementation produces "key="
    assert result == 'key=', f"None not handled as documented: {result!r}"

# Test: asbool with numeric strings
@given(st.integers())
def test_asbool_numeric_strings(num):
    """Test asbool with numeric strings."""
    str_num = str(num)
    result = pyramid_settings.asbool(str_num)
    
    # Only '1' should be truthy, everything else falsy
    if str_num == '1':
        assert result is True
    elif str_num == '0':
        assert result is False
    else:
        # Other numbers are not in truthy set, should be False
        assert result is False

# Test: Check urlencode with very long values
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.text(min_size=10000, max_size=10001),  # Very long values
        max_size=1
    )
)
@settings(max_examples=10)
def test_urlencode_long_values(data):
    """Test urlencode doesn't have issues with very long values."""
    result = encode.urlencode(data)
    assert isinstance(result, str)
    assert len(result) > 10000  # Should include the long value

# Test edge case: What if quote_via raises an exception?
def test_urlencode_with_failing_quote():
    """Test urlencode when quote_via function fails."""
    def bad_quote(val):
        raise ValueError("Intentional error")
    
    data = {'key': 'value'}
    try:
        result = encode.urlencode(data, quote_via=bad_quote)
        assert False, f"Should have raised error, got: {result}"
    except ValueError as e:
        assert str(e) == "Intentional error"

# Test: Check inconsistency between docstring and code for None values
def test_none_handling_documentation_bug():
    """
    The docstring says None values are 'dropped' but the code shows
    they produce 'key=' in the output. This is a documentation bug.
    """
    # Single None value
    result1 = encode.urlencode({'a': None})
    print(f"urlencode({{'a': None}}): {result1!r}")
    
    # None with other values  
    result2 = encode.urlencode({'a': None, 'b': 'val'})
    print(f"urlencode({{'a': None, 'b': 'val'}}): {result2!r}")
    
    # Multiple None values
    result3 = encode.urlencode({'a': None, 'b': None})
    print(f"urlencode({{'a': None, 'b': None}}): {result3!r}")
    
    # If None values were truly "dropped" as docs claim:
    # - result1 would be '' (empty)
    # - result2 would be 'b=val' (no 'a')
    # - result3 would be '' (empty)
    
    # But actual behavior includes them as 'key='
    assert 'a=' in result1, "None value not in output"
    assert 'a=' in result2, "None value not in output"
    assert 'a=' in result3, "None value not in output"
    
    print("\nDOCUMENTATION BUG CONFIRMED:")
    print("Docstring claims None values are 'dropped', but they actually produce 'key=' in output")

if __name__ == '__main__':
    print("=== Testing edge cases ===\n")
    
    test_urlencode_empty_vs_none_detailed()
    print()
    
    test_urlencode_none_not_dropped()
    print()
    
    test_none_handling_documentation_bug()
    print()
    
    test_urlencode_with_failing_quote()
    print("Quote function error handling: OK")
    
    # Run hypothesis tests
    import pytest
    pytest.main([__file__, '-v', '-k', 'not test_none_handling', '--tb=short'])