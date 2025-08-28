#!/usr/bin/env python3
"""Run property-based tests for Python Fire without pytest."""

import traceback
from hypothesis import given, strategies as st, settings, assume
import fire
import fire.parser as parser


def run_test(test_func, test_name):
    """Run a single property test and report results."""
    print(f"\nTesting: {test_name}")
    try:
        # Run the test with hypothesis
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except AssertionError as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ {test_name} ERROR")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False


# Test functions for property testing
def simple_function(x=10):
    """A simple function that returns its input."""
    return x


class SimpleClass:
    """A simple class for testing."""
    
    def __init__(self, value=100):
        self.value = value
    
    def double(self, x=1):
        return 2 * x
    
    def add(self, a, b=10):
        return a + b


# Test 1: Integer preservation
@given(st.integers(min_value=-10000, max_value=10000))
@settings(max_examples=100)
def test_integer_preservation(value):
    """Test that integer values are correctly parsed and preserved."""
    result = fire.Fire(simple_function, command=[str(value)])
    assert result == value, f"Expected {value}, got {result}"
    assert type(result) == int, f"Expected int, got {type(result)}"


# Test 2: Float preservation
@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_float_preservation(value):
    """Test that float values are correctly parsed and preserved."""
    str_value = str(value)
    result = fire.Fire(simple_function, command=[str_value])
    # Use tolerance for float comparison
    assert abs(result - value) < 1e-10 or str(result) == str(value), f"Expected {value}, got {result}"


# Test 3: Boolean parsing
@given(st.booleans())
@settings(max_examples=10)
def test_boolean_parsing(value):
    """Test that boolean values are correctly parsed."""
    bool_str = 'True' if value else 'False'
    result = fire.Fire(simple_function, command=[bool_str])
    assert result == value, f"Expected {value}, got {result}"
    assert type(result) == bool, f"Expected bool, got {type(result)}"


# Test 4: List parsing
@given(st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=5))
@settings(max_examples=50)
def test_list_parsing(lst):
    """Test that list literals are correctly parsed."""
    list_str = str(lst)
    result = fire.Fire(simple_function, command=[list_str])
    assert result == lst, f"Expected {lst}, got {result}"
    assert type(result) == list, f"Expected list, got {type(result)}"


# Test 5: Dictionary parsing
@given(
    st.dictionaries(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=3),
        st.integers(min_value=-100, max_value=100),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=50)
def test_dict_parsing(dct):
    """Test that dictionary literals are correctly parsed."""
    dict_str = str(dct)
    result = fire.Fire(simple_function, command=[dict_str])
    assert result == dct, f"Expected {dct}, got {result}"
    assert type(result) == dict, f"Expected dict, got {type(result)}"


# Test 6: Quoted string handling
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789 ', min_size=1, max_size=10))
@settings(max_examples=50)
def test_quoted_string_handling(text):
    """Test that quoted strings are handled correctly."""
    quoted_text = f'"{text}"'
    result = fire.Fire(simple_function, command=[quoted_text])
    assert result == text, f"Expected '{text}', got '{result}'"


# Test 7: Flag consistency
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100)
)
@settings(max_examples=50)
def test_flag_argument_consistency(val1, val2):
    """Test that --flag=value and --flag value produce the same result."""
    obj = SimpleClass()
    
    # Test with equals sign
    command_equals = ['add', str(val1), f'--b={val2}']
    # Test without equals sign
    command_space = ['add', str(val1), '--b', str(val2)]
    
    try:
        result_equals = fire.Fire(obj, command=command_equals)
        result_space = fire.Fire(obj, command=command_space)
        assert result_equals == result_space, f"Results differ: {result_equals} != {result_space}"
    except (fire.core.FireExit, SystemExit) as e1:
        # If one fails, both should fail
        try:
            fire.Fire(obj, command=command_space)
            assert False, "Expected both commands to fail"
        except (fire.core.FireExit, SystemExit):
            pass


# Test 8: Parser idempotence
@given(st.integers(min_value=-1000, max_value=1000))
@settings(max_examples=100)
def test_parsing_idempotence(value):
    """Test that parsing a value multiple times gives consistent results."""
    str_value = str(value)
    parsed1 = parser.DefaultParseValue(str_value)
    parsed2 = parser.DefaultParseValue(str_value)
    assert parsed1 == parsed2, f"Parsing not idempotent: {parsed1} != {parsed2}"
    assert type(parsed1) == type(parsed2), f"Types differ: {type(parsed1)} != {type(parsed2)}"


# Test 9: SeparateFlagArgs
@given(st.lists(st.sampled_from(['arg1', 'arg2', '--flag', 'value', '--', 'more']), min_size=0, max_size=10))
@settings(max_examples=100)
def test_separate_flag_args(args):
    """Test that SeparateFlagArgs correctly splits arguments."""
    fire_args, flag_args = parser.SeparateFlagArgs(args)
    
    # Invariant: if no '--' in args, all args are fire args
    if '--' not in args:
        assert fire_args == args, f"Expected all args to be fire args"
        assert flag_args == [], f"Expected no flag args"
    else:
        # The recombined args should match the split
        last_separator_idx = len(args) - 1 - args[::-1].index('--')
        assert fire_args == args[:last_separator_idx], f"Fire args mismatch"
        assert flag_args == args[last_separator_idx + 1:], f"Flag args mismatch"


# Test 10: Special case - negative numbers
@given(st.integers(min_value=-1000, max_value=-1))
@settings(max_examples=50)
def test_negative_number_parsing(value):
    """Test that negative numbers are correctly parsed."""
    result = fire.Fire(simple_function, command=[str(value)])
    assert result == value, f"Expected {value}, got {result}"
    assert type(result) == int, f"Expected int, got {type(result)}"


def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("Running Property-Based Tests for Python Fire")
    print("=" * 60)
    
    tests = [
        (test_integer_preservation, "Integer preservation"),
        (test_float_preservation, "Float preservation"),
        (test_boolean_parsing, "Boolean parsing"),
        (test_list_parsing, "List literal parsing"),
        (test_dict_parsing, "Dictionary literal parsing"),
        (test_quoted_string_handling, "Quoted string handling"),
        (test_flag_argument_consistency, "Flag argument consistency"),
        (test_parsing_idempotence, "Parser idempotence"),
        (test_separate_flag_args, "SeparateFlagArgs function"),
        (test_negative_number_parsing, "Negative number parsing"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\n⚠️ Some tests failed. Review the errors above.")
    else:
        print("\n✅ All tests passed!")


if __name__ == '__main__':
    main()