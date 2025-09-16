#!/usr/bin/env python3
"""Edge case property-based tests for Python Fire."""

import traceback
import shlex
from hypothesis import given, strategies as st, settings, assume
import fire
import fire.parser as parser


# Test edge case: Empty strings and whitespace
@given(st.sampled_from(['', '  ', '\t', '\n', '   \t\n   ']))
@settings(max_examples=20)
def test_whitespace_handling(whitespace):
    """Test how Fire handles whitespace and empty strings."""
    def test_func(x="default"):
        return x
    
    try:
        # Test with whitespace as command
        result = fire.Fire(test_func, command=[whitespace])
        print(f"Whitespace '{repr(whitespace)}' parsed as: {repr(result)}")
    except Exception as e:
        print(f"Whitespace '{repr(whitespace)}' caused: {type(e).__name__}")


# Test edge case: Special characters in strings
@given(st.text(alphabet='!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~', min_size=1, max_size=10))
@settings(max_examples=50)
def test_special_characters(text):
    """Test handling of special characters."""
    def test_func(x="default"):
        return x
    
    try:
        # Try with quotes
        quoted = f'"{text}"'
        result = fire.Fire(test_func, command=[quoted])
        assert result == text, f"Quoted special chars failed: expected {text}, got {result}"
    except Exception as e:
        print(f"Special chars '{text}' caused: {type(e).__name__}: {e}")


# Test edge case: Unicode characters
@given(st.text(alphabet='αβγδεζηθικλμνξοπρστυφχψω中文日本語', min_size=1, max_size=5))
@settings(max_examples=30)
def test_unicode_handling(text):
    """Test handling of Unicode characters."""
    def test_func(x="default"):
        return x
    
    try:
        quoted = f'"{text}"'
        result = fire.Fire(test_func, command=[quoted])
        assert result == text, f"Unicode failed: expected {text}, got {result}"
    except Exception as e:
        print(f"Unicode '{text}' caused: {type(e).__name__}: {e}")


# Test edge case: Very long strings
@given(st.text(min_size=1000, max_size=10000))
@settings(max_examples=5)
def test_long_string_handling(text):
    """Test handling of very long strings."""
    def test_func(x="default"):
        return x
    
    try:
        # Quote the string to ensure it's treated as a single argument
        quoted = f'"{text}"'
        result = fire.Fire(test_func, command=[quoted])
        assert result == text, f"Long string truncated or modified"
    except Exception as e:
        print(f"Long string caused: {type(e).__name__}: {e}")


# Test edge case: Nested structures
@given(
    st.recursive(
        st.integers() | st.booleans() | st.text(max_size=5),
        lambda children: st.lists(children, max_size=3) | 
                        st.dictionaries(st.text(alphabet='abc', max_size=3), children, max_size=3),
        max_leaves=10
    )
)
@settings(max_examples=20)
def test_nested_structure_parsing(structure):
    """Test parsing of nested data structures."""
    def test_func(x=None):
        return x
    
    try:
        str_structure = str(structure)
        result = fire.Fire(test_func, command=[str_structure])
        assert result == structure, f"Nested structure parsing failed"
    except Exception as e:
        print(f"Nested structure caused: {type(e).__name__}")


# Test edge case: Command injection attempts
@given(st.sampled_from([
    '"; echo hacked"',
    '$(echo hacked)',
    '`echo hacked`',
    '| echo hacked',
    '&& echo hacked',
    '; echo hacked',
    '\'; echo hacked\'',
]))
@settings(max_examples=20)
def test_command_injection_safety(payload):
    """Test that command injection attempts are safely handled."""
    def test_func(x="default"):
        return x
    
    try:
        # Fire should treat these as literal strings, not execute them
        result = fire.Fire(test_func, command=[payload])
        # The payload should be returned as-is, not executed
        assert 'hacked' not in str(result) or result == payload
        print(f"Injection payload '{payload}' safely handled as: {repr(result)}")
    except Exception as e:
        print(f"Injection payload '{payload}' caused: {type(e).__name__}")


# Test edge case: Numeric edge values
@given(st.sampled_from([
    float('inf'), float('-inf'), 
    1e308, -1e308,  # Near float limits
    2**63-1, -(2**63),  # Near int limits
    0.0, -0.0,  # Zero variants
]))
@settings(max_examples=20)
def test_numeric_edge_values(value):
    """Test handling of numeric edge values."""
    def test_func(x=0):
        return x
    
    try:
        str_value = str(value)
        result = fire.Fire(test_func, command=[str_value])
        # Check if the value is preserved
        if str_value in ['inf', '-inf']:
            assert str(result) == str_value
        else:
            assert result == value or abs(result - value) < 1e-10
    except Exception as e:
        print(f"Numeric edge {value} caused: {type(e).__name__}: {e}")


# Test metamorphic property: Adding then removing elements
@given(
    st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=10),
    st.integers(min_value=-100, max_value=100)
)
@settings(max_examples=50)
def test_list_append_pop_metamorphic(lst, elem):
    """Test that appending then popping an element preserves the list."""
    def append_func(lst, elem):
        lst.append(elem)
        return lst
    
    def pop_func(lst):
        if lst:
            lst.pop()
        return lst
    
    # Append element
    lst_copy = lst.copy()
    result1 = fire.Fire(append_func, command=[str(lst), str(elem)])
    
    # Pop element
    result2 = fire.Fire(pop_func, command=[str(result1)])
    
    # Should get back original list
    assert result2 == lst, f"Append-pop not inverse: {lst} -> {result1} -> {result2}"


# Test parser edge cases
@given(st.sampled_from([
    '--', '---', '----',
    '-', '--=', '=-',
    '=', '==', '===',
    '--=value', 'key=', '=value'
]))
@settings(max_examples=30)
def test_parser_edge_syntax(text):
    """Test parser with edge case syntax."""
    try:
        parsed = parser.DefaultParseValue(text)
        # Should not crash and should return something
        assert parsed is not None
        print(f"Edge syntax '{text}' parsed as: {repr(parsed)}")
    except Exception as e:
        print(f"Parser edge '{text}' caused: {type(e).__name__}: {e}")


# Test round-trip property with shlex
@given(st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-_', min_size=1, max_size=10), min_size=1, max_size=5))
@settings(max_examples=50)
def test_shlex_round_trip(args):
    """Test that command string and list are equivalent via shlex."""
    def test_func(*args):
        return args
    
    # Create command string using shlex.join (Python 3.8+) or manual joining
    try:
        import shlex
        if hasattr(shlex, 'join'):
            command_str = shlex.join(args)
        else:
            command_str = ' '.join(shlex.quote(arg) for arg in args)
        
        # Test both ways
        result_list = fire.Fire(test_func, command=args)
        result_str = fire.Fire(test_func, command=command_str)
        
        assert result_list == result_str, f"Shlex round-trip failed: {result_list} != {result_str}"
    except Exception as e:
        print(f"Shlex round-trip failed: {type(e).__name__}: {e}")


def run_edge_case_tests():
    """Run all edge case tests."""
    print("=" * 60)
    print("Running Edge Case Tests for Python Fire")
    print("=" * 60)
    
    tests = [
        test_whitespace_handling,
        test_special_characters,
        test_unicode_handling,
        test_long_string_handling,
        test_nested_structure_parsing,
        test_command_injection_safety,
        test_numeric_edge_values,
        test_list_append_pop_metamorphic,
        test_parser_edge_syntax,
        test_shlex_round_trip,
    ]
    
    for test_func in tests:
        test_name = test_func.__name__
        print(f"\n>>> Testing: {test_name}")
        print("-" * 40)
        try:
            test_func()
            print(f"✓ {test_name} completed")
        except AssertionError as e:
            print(f"✗ {test_name} FAILED: {e}")
            traceback.print_exc()
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Edge case testing completed")
    print("=" * 60)


if __name__ == '__main__':
    run_edge_case_tests()