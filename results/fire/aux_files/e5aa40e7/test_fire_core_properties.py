"""Property-based tests for fire.core module using Hypothesis."""

import sys
import json
import inspect
import types
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import fire.core as core


# Test 1: _IsFlag should NOT identify negative numbers as flags (per docstring)
@given(st.integers(min_value=-999999, max_value=-1))
def test_negative_numbers_not_flags(num):
    """Test that negative numbers are not identified as flags.
    
    The docstring for _IsFlag states: 
    'If it starts with a hyphen and isn't a negative number, it's a flag.'
    
    This means negative numbers should NOT be identified as flags.
    """
    arg = str(num)
    result = core._IsFlag(arg)
    assert not result, f"Negative number {arg} was incorrectly identified as a flag"


# Test 2: _OneLineResult should always return a single line (no newlines)
@given(st.one_of(
    st.text(min_size=0, max_size=1000),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.integers()),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers()),
    st.tuples(st.integers(), st.text()),
))
def test_one_line_result_single_line(value):
    """Test that _OneLineResult always returns a string without newlines."""
    result = core._OneLineResult(value)
    assert isinstance(result, str), f"Result should be a string, got {type(result)}"
    assert '\n' not in result, f"Result contains newline: {repr(result)}"


# Test 3: Test for overlap between single and multi char flag functions
@given(st.text(min_size=1, max_size=20))
def test_flag_function_consistency(arg):
    """Test the relationship between flag detection functions.
    
    If _IsSingleCharFlag returns True, then _IsFlag must also return True.
    If _IsMultiCharFlag returns True, then _IsFlag must also return True.
    """
    is_single = core._IsSingleCharFlag(arg)
    is_multi = core._IsMultiCharFlag(arg)
    is_flag = core._IsFlag(arg)
    
    # Property: if something is a single char flag, it must be a flag
    if is_single:
        assert is_flag, f"Single char flag {arg} not recognized by _IsFlag"
    
    # Property: if something is a multi char flag, it must be a flag
    if is_multi:
        assert is_flag, f"Multi char flag {arg} not recognized by _IsFlag"
    
    # Property: _IsFlag should be True iff at least one of the others is True
    assert is_flag == (is_single or is_multi), \
        f"Inconsistent flag detection for {arg}: is_flag={is_flag}, is_single={is_single}, is_multi={is_multi}"


# Test 4: Test specific negative number edge cases
@given(st.integers(min_value=0, max_value=999999))
def test_negative_number_strings_as_flags(num):
    """Test that strings starting with '-' followed by digits are incorrectly treated as flags."""
    arg = f"-{num}"
    # According to the docstring, negative numbers should NOT be flags
    # But let's see what actually happens
    result = core._IsFlag(arg)
    # This test will likely fail, exposing the bug
    assert not result, f"String '{arg}' (negative number) incorrectly identified as flag"


# Test 5: Round-trip property for _OneLineResult with JSON-serializable objects
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100),
    st.lists(st.integers(), max_size=10),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=5)
))
def test_one_line_result_json_parseable(value):
    """For JSON-serializable values, _OneLineResult should produce valid JSON."""
    result = core._OneLineResult(value)
    
    # Skip this test for strings, as they're handled specially
    if isinstance(value, str):
        return
    
    # Try to parse the result as JSON
    try:
        parsed = json.loads(result)
        # For simple types, the parsed value should match the original
        if isinstance(value, (int, float, list, dict)):
            assert parsed == value, f"JSON round-trip failed: {value} -> {result} -> {parsed}"
    except (json.JSONDecodeError, ValueError):
        # Some results might not be JSON (like function/module representations)
        # That's okay, but let's make sure they don't have newlines
        assert '\n' not in result


# Test 6: Test that multi-line strings get converted to single line
@given(st.text(min_size=0, max_size=100))
def test_one_line_result_removes_newlines_from_strings(text):
    """Test that strings with newlines get converted to single line."""
    # Add some newlines to the text
    text_with_newlines = text.replace(' ', '\n', 1) if ' ' in text else text + '\n'
    
    result = core._OneLineResult(text_with_newlines)
    
    # The newlines should be replaced with spaces
    assert '\n' not in result
    # For strings, newlines should be replaced with spaces
    if '\n' in text_with_newlines:
        expected = text_with_newlines.replace('\n', ' ')
        assert result == expected


if __name__ == "__main__":
    print("Running property-based tests for fire.core...")
    
    # Run each test with explicit output
    tests = [
        ("Negative numbers as flags", test_negative_numbers_not_flags),
        ("OneLineResult single line", test_one_line_result_single_line),
        ("Flag function consistency", test_flag_function_consistency),
        ("Negative number strings", test_negative_number_strings_as_flags),
        ("OneLineResult JSON parseable", test_one_line_result_json_parseable),
        ("OneLineResult removes newlines", test_one_line_result_removes_newlines_from_strings)
    ]
    
    for name, test_func in tests:
        print(f"\nTesting: {name}")
        try:
            test_func()
            print(f"  ✓ Passed")
        except AssertionError as e:
            print(f"  ✗ Failed: {e}")
        except Exception as e:
            print(f"  ✗ Error: {e}")