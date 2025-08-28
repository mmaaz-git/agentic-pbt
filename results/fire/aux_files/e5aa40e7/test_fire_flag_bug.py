"""Test to expose the None return value bug in fire.core flag functions."""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import fire.core as core


@given(st.text(min_size=1, max_size=20))
def test_flag_functions_return_boolean_not_none(arg):
    """Test that flag detection functions return boolean values, not None.
    
    These functions claim to return booleans per their docstrings,
    but they can actually return None in some cases.
    """
    # Test _IsSingleCharFlag
    result_single = core._IsSingleCharFlag(arg)
    assert result_single is True or result_single is False, \
        f"_IsSingleCharFlag('{arg}') returned {result_single} (type: {type(result_single)}), expected bool"
    
    # Test _IsMultiCharFlag  
    result_multi = core._IsMultiCharFlag(arg)
    assert result_multi is True or result_multi is False, \
        f"_IsMultiCharFlag('{arg}') returned {result_multi} (type: {type(result_multi)}), expected bool"
    
    # Test _IsFlag
    result_flag = core._IsFlag(arg)
    assert result_flag is True or result_flag is False, \
        f"_IsFlag('{arg}') returned {result_flag} (type: {type(result_flag)}), expected bool"


# Test specific cases that trigger the bug
def test_negative_numbers_return_none():
    """Test that negative number strings cause None to be returned."""
    test_cases = ['-1', '-123', '-999', '-0']
    
    for test in test_cases:
        result = core._IsMultiCharFlag(test)
        print(f"_IsMultiCharFlag('{test}') = {result} (type: {type(result)})")
        # This will fail because it returns None, not False
        assert result is False, f"Expected False for '{test}', got {result}"


if __name__ == "__main__":
    print("Testing for None return values in flag functions...")
    
    # First show the bug with specific examples
    print("\nDemonstrating the bug with specific inputs:")
    try:
        test_negative_numbers_return_none()
    except AssertionError as e:
        print(f"Bug found: {e}")
    
    # Then run the property test
    print("\nRunning property-based test:")
    try:
        test_flag_functions_return_boolean_not_none()
        print("Test passed")
    except AssertionError as e:
        print(f"Bug found: {e}")