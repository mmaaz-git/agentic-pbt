#!/usr/bin/env python3
"""Focused bug-hunting tests for Python Fire based on implementation analysis."""

import sys
import traceback
from hypothesis import given, strategies as st, settings, assume, example
import fire
import fire.parser as parser
import fire.core


# Bug Hunt 1: Test for inconsistencies in boolean flag parsing
@given(st.sampled_from(['--arg', '--noarg', '-arg', '-noarg']))
@settings(max_examples=50)
def test_boolean_no_prefix_consistency(flag):
    """Test that 'no' prefix for boolean flags works consistently."""
    def test_func(arg=False):
        return arg
    
    result = fire.Fire(test_func, command=[flag])
    
    # --arg and -arg should give True
    # --noarg and -noarg should give False
    if 'no' in flag:
        assert result == False, f"Flag {flag} should give False, got {result}"
    else:
        assert result == True, f"Flag {flag} should give True, got {result}"


# Bug Hunt 2: Float-int coercion edge cases
@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
@example(3.0)  # Exact integer as float
@example(3.14159)  # Non-integer float
@example(1e10)  # Large float
@example(0.1)  # Small decimal
def test_float_int_coercion(value):
    """Test how Fire handles float values for int parameters."""
    def int_func(x: int):
        return x
    
    try:
        result = fire.Fire(int_func, command=[str(value)])
        # If it succeeds, check the type
        if value == int(value):  # If value is actually an integer
            assert type(result) == int or type(result) == float
        else:
            # Non-integer floats might be coerced or cause an error
            assert type(result) in [int, float]
    except (fire.core.FireExit, SystemExit, ValueError):
        # Some float values might legitimately fail for int parameters
        pass


# Bug Hunt 3: Separator edge cases
@given(
    st.lists(st.sampled_from(['arg', '--flag', 'value', '-', '--']), min_size=2, max_size=10)
)
@settings(max_examples=100)
def test_separator_parsing_edge_cases(args):
    """Test edge cases in separator parsing."""
    def test_func(x="default"):
        return x
    
    try:
        # Multiple separators should be handled correctly
        result = fire.Fire(test_func, command=args)
        # Should not crash
        assert result is not None
    except (fire.core.FireExit, SystemExit):
        # Some combinations might fail, which is fine
        pass


# Bug Hunt 4: Quote handling inconsistencies
@given(
    st.sampled_from([
        "'single'",
        '"double"',
        '"""triple"""',
        "'''triple single'''",
        '"\'"',  # Quote within quotes
        '"\\n"',  # Escape sequences
        '""',  # Empty quotes
        "''",  # Empty single quotes
    ])
)
@settings(max_examples=50)
def test_quote_parsing_consistency(quoted_str):
    """Test that different quote styles are handled consistently."""
    def test_func(x="default"):
        return x
    
    try:
        result = fire.Fire(test_func, command=[quoted_str])
        # Result should be a string with quotes stripped
        assert isinstance(result, str), f"Expected string, got {type(result)}"
        # Should not include the outer quotes
        assert not (result.startswith('"') and result.endswith('"'))
        assert not (result.startswith("'") and result.endswith("'"))
    except Exception as e:
        print(f"Quote parsing '{quoted_str}' failed: {e}")


# Bug Hunt 5: Class instantiation with various argument styles
@given(
    st.dictionaries(
        st.sampled_from(['arg1', 'arg2', 'arg3']),
        st.integers(min_value=-100, max_value=100),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=50)
def test_class_instantiation_kwargs(kwargs):
    """Test class instantiation with keyword arguments."""
    class TestClass:
        def __init__(self, arg1=1, arg2=2, arg3=3):
            self.arg1 = arg1
            self.arg2 = arg2
            self.arg3 = arg3
        
        def get_sum(self):
            return self.arg1 + self.arg2 + self.arg3
    
    # Build command with keyword arguments
    command = []
    for key, value in kwargs.items():
        command.extend([f'--{key}', str(value)])
    command.append('-')
    command.append('get_sum')
    
    try:
        result = fire.Fire(TestClass, command=command)
        # Calculate expected sum
        expected = kwargs.get('arg1', 1) + kwargs.get('arg2', 2) + kwargs.get('arg3', 3)
        assert result == expected, f"Expected {expected}, got {result}"
    except (fire.core.FireExit, SystemExit) as e:
        print(f"Class instantiation failed with {kwargs}: {e}")


# Bug Hunt 6: Parser._LiteralEval edge cases
@given(st.sampled_from([
    '{a: b}',  # Bareword dict keys
    '[a, b, c]',  # Bareword list items  
    '{1: a, 2: b}',  # Mixed barewords and literals
    '(a, b)',  # Bareword tuples
    '{a: {b: c}}',  # Nested barewords
    '[]',  # Empty list
    '{}',  # Empty dict
    '()',  # Empty tuple
]))
@settings(max_examples=50)
def test_literal_eval_barewords(expr):
    """Test _LiteralEval with bareword expressions."""
    try:
        result = parser.DefaultParseValue(expr)
        # Should successfully parse these YAML-like expressions
        assert result is not None
        print(f"Bareword expr '{expr}' parsed as: {result}")
    except Exception as e:
        print(f"Bareword parsing '{expr}' failed: {type(e).__name__}: {e}")


# Bug Hunt 7: Ambiguous flag shortcuts
@given(
    st.lists(
        st.sampled_from(['-a', '-al', '-alpha', '--alpha', '-b', '-be', '-beta', '--beta']),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=50)
def test_ambiguous_flag_shortcuts(flags):
    """Test handling of ambiguous single-character flag shortcuts."""
    def test_func(alpha=False, alpha_long=False, beta=False, beta_long=False):
        return {'alpha': alpha, 'alpha_long': alpha_long, 'beta': beta, 'beta_long': beta_long}
    
    try:
        result = fire.Fire(test_func, command=flags)
        # Should handle shortcuts without crashing
        assert isinstance(result, dict)
    except (fire.core.FireExit, SystemExit):
        # Ambiguous shortcuts might cause legitimate errors
        pass


# Bug Hunt 8: Mixed positional and keyword arguments
@given(
    st.integers(min_value=-100, max_value=100),
    st.integers(min_value=-100, max_value=100),
    st.booleans()
)
@settings(max_examples=100)
def test_mixed_args_ordering(pos_val, kw_val, use_kw_first):
    """Test mixing positional and keyword arguments in different orders."""
    def test_func(pos, kw=10):
        return pos + kw
    
    if use_kw_first:
        # Keyword before positional
        command = [f'--kw={kw_val}', str(pos_val)]
    else:
        # Positional before keyword  
        command = [str(pos_val), f'--kw={kw_val}']
    
    try:
        result = fire.Fire(test_func, command=command)
        expected = pos_val + kw_val
        assert result == expected, f"Expected {expected}, got {result}"
    except (fire.core.FireExit, SystemExit) as e:
        # This might fail in some cases
        print(f"Mixed args failed: {command} -> {e}")


# Bug Hunt 9: Command chaining with errors
@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_chaining_with_errors(value):
    """Test command chaining when intermediate commands might fail."""
    class Chain:
        def get_dict(self):
            return {'key': value}
        
        def get_none(self):
            return None
        
        def get_list(self):
            return [1, 2, 3]
    
    # Try to chain through None (should fail)
    try:
        result = fire.Fire(Chain, command=['get_none', '-', 'some_method'])
        # Should not succeed
        assert False, "Expected chaining through None to fail"
    except (fire.core.FireExit, SystemExit, AttributeError):
        # Expected to fail
        pass
    
    # Try to chain through dict
    try:
        result = fire.Fire(Chain, command=['get_dict', '-', 'key'])
        assert result == value, f"Dict chaining failed: expected {value}, got {result}"
    except (fire.core.FireExit, SystemExit):
        print(f"Dict chaining unexpectedly failed")


# Bug Hunt 10: Type annotation enforcement
@given(
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(min_size=1, max_size=10),
        st.booleans()
    )
)
@settings(max_examples=100)
def test_type_annotation_coercion(value):
    """Test how Fire handles type annotations for coercion."""
    def typed_func(x: int):
        return x * 2
    
    try:
        result = fire.Fire(typed_func, command=[str(value)])
        # If it succeeds, the value should have been coerced to int
        assert isinstance(result, int) or isinstance(result, float)
        # The result should be twice the integer value
        if isinstance(value, (int, float)):
            expected = int(value) * 2
            assert abs(result - expected) < 1, f"Expected ~{expected}, got {result}"
    except (fire.core.FireExit, SystemExit, ValueError, TypeError):
        # Non-numeric values should fail
        if isinstance(value, (int, float)):
            print(f"Unexpected failure for numeric value {value}")


def run_bug_hunt():
    """Run all bug hunting tests."""
    print("=" * 60)
    print("Bug Hunting Tests for Python Fire")
    print("=" * 60)
    
    tests = [
        (test_boolean_no_prefix_consistency, "Boolean 'no' prefix consistency"),
        (test_float_int_coercion, "Float-int coercion"),
        (test_separator_parsing_edge_cases, "Separator parsing edge cases"),
        (test_quote_parsing_consistency, "Quote parsing consistency"),
        (test_class_instantiation_kwargs, "Class instantiation with kwargs"),
        (test_literal_eval_barewords, "Bareword literal evaluation"),
        (test_ambiguous_flag_shortcuts, "Ambiguous flag shortcuts"),
        (test_mixed_args_ordering, "Mixed positional/keyword argument ordering"),
        (test_chaining_with_errors, "Command chaining error handling"),
        (test_type_annotation_coercion, "Type annotation coercion"),
    ]
    
    bugs_found = []
    
    for test_func, test_name in tests:
        print(f"\n>>> {test_name}")
        print("-" * 40)
        try:
            test_func()
            print(f"✓ No bugs found")
        except AssertionError as e:
            print(f"🐛 POTENTIAL BUG FOUND: {e}")
            bugs_found.append((test_name, str(e)))
            traceback.print_exc()
        except Exception as e:
            print(f"✗ Test error: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Bug hunt completed. Found {len(bugs_found)} potential issues.")
    
    if bugs_found:
        print("\nPotential bugs found:")
        for name, error in bugs_found:
            print(f"  - {name}: {error}")
    
    print("=" * 60)
    
    return bugs_found


if __name__ == '__main__':
    bugs = run_bug_hunt()
    sys.exit(0 if not bugs else 1)