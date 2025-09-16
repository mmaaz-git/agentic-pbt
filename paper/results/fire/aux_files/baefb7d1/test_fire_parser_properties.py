#!/usr/bin/env python3
"""Property-based tests for fire.parser module."""

import ast
import math
from hypothesis import assume, given, strategies as st, settings
import fire.parser as parser


@given(st.lists(st.text(min_size=1).filter(lambda x: x != '--')))
def test_separate_flag_args_reconstruction(args):
    """Test that SeparateFlagArgs correctly splits and we can reconstruct."""
    fire_args, flag_args = parser.SeparateFlagArgs(args)
    
    # Property: The total number of arguments should be preserved (minus separators)
    separators_count = args.count('--')
    if separators_count > 0:
        # When there's a separator, we lose it in the split
        assert len(fire_args) + len(flag_args) == len(args) - 1
    else:
        # When there's no separator, all args go to fire_args
        assert fire_args == args
        assert flag_args == []


@given(st.lists(st.text(min_size=1)))
def test_separate_flag_args_last_separator(args):
    """Test that only the LAST '--' is used as separator."""
    fire_args, flag_args = parser.SeparateFlagArgs(args)
    
    if '--' in args:
        # Find the last '--' index
        last_sep_idx = len(args) - 1 - args[::-1].index('--')
        
        # Property: Everything before last '--' should be in fire_args
        assert fire_args == args[:last_sep_idx]
        # Property: Everything after last '--' should be in flag_args  
        assert flag_args == args[last_sep_idx + 1:]


@given(st.integers())
def test_default_parse_value_integer_identity(n):
    """Test that parsing an integer string gives back the integer."""
    result = parser.DefaultParseValue(str(n))
    assert result == n
    assert isinstance(result, int)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_default_parse_value_float_round_trip(f):
    """Test float parsing round-trip."""
    # Skip floats that have representation issues
    assume(not math.isnan(f))
    assume(not math.isinf(f))
    
    f_str = str(f)
    result = parser.DefaultParseValue(f_str)
    
    # The result should be close to the original float
    if isinstance(result, (int, float)):
        if '.' in f_str or 'e' in f_str.lower():
            assert math.isclose(result, f, rel_tol=1e-9)


@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_default_parse_value_list_structure(lst):
    """Test that list literals are parsed correctly."""
    list_str = str(lst)
    result = parser.DefaultParseValue(list_str)
    
    # Property: Parsed list should equal original
    assert result == lst
    assert isinstance(result, list)


@given(st.dictionaries(st.text(st.characters(blacklist_categories=['Cc', 'Cs'], min_codepoint=32), min_size=1, max_size=10).filter(lambda x: x.isidentifier()), 
                        st.integers(), min_size=0, max_size=5))
def test_default_parse_value_dict_structure(d):
    """Test dict parsing with valid Python identifiers as keys."""
    # Create dict string with quotes around keys
    dict_str = '{' + ', '.join(f'"{k}": {v}' for k, v in d.items()) + '}'
    result = parser.DefaultParseValue(dict_str)
    
    assert result == d
    assert isinstance(result, dict)


@given(st.text(alphabet=st.characters(blacklist_categories=['Cc'], min_codepoint=32, max_codepoint=126), min_size=1))
def test_default_parse_value_single_vs_double_quotes(s):
    """Test that single and double quotes behave consistently."""
    # Skip strings that contain quotes themselves
    assume('"' not in s)
    assume("'" not in s)
    assume('\\' not in s)
    
    single_quoted = f"'{s}'"
    double_quoted = f'"{s}"'
    
    result_single = parser.DefaultParseValue(single_quoted)
    result_double = parser.DefaultParseValue(double_quoted)
    
    # Property: Both quote styles should give the same result
    assert result_single == result_double
    assert result_single == s


@given(st.text(min_size=1).filter(lambda x: not any(c in x for c in ['"', "'", '\\', '(', ')', '[', ']', '{', '}', ',', ':', '#'])))
def test_default_parse_value_bareword_as_string(s):
    """Test that bare words without special chars are treated as strings."""
    # Skip Python keywords that would be parsed differently
    assume(s not in ['True', 'False', 'None'])
    # Skip things that look like numbers
    try:
        float(s)
        assume(False)
    except ValueError:
        pass
    
    result = parser.DefaultParseValue(s)
    
    # Property: Bare words should be returned as strings unchanged
    assert result == s
    assert isinstance(result, str)


@given(st.lists(st.text(st.characters(blacklist_categories=['Cc'], min_codepoint=32, max_codepoint=126), min_size=1, max_size=5).filter(lambda x: x.isidentifier()),
                min_size=1, max_size=5))
def test_literal_eval_bareword_conversion(identifiers):
    """Test that _LiteralEval converts bare identifiers to strings in lists."""
    # Create a list with bare identifiers
    list_str = '[' + ', '.join(identifiers) + ']'
    
    # This should parse the identifiers as strings
    result = parser.DefaultParseValue(list_str)
    
    # Property: All identifiers should be converted to strings (except True/False/None)
    expected = []
    for ident in identifiers:
        if ident in ('True', 'False', 'None'):
            expected.append(eval(ident))
        else:
            expected.append(ident)
    
    assert result == expected


@given(st.tuples(st.integers(), st.integers()))
def test_default_parse_value_tuple_structure(tup):
    """Test tuple parsing."""
    tuple_str = str(tup)
    result = parser.DefaultParseValue(tuple_str)
    
    # Property: Should preserve tuple structure
    assert result == tup
    assert isinstance(result, tuple)


@given(st.text())
def test_default_parse_value_never_crashes(s):
    """Test that DefaultParseValue never crashes on any input."""
    try:
        result = parser.DefaultParseValue(s)
        # Property: Should always return something
        assert result is not None or s == 'None'
    except (TypeError, MemoryError, RecursionError):
        # These are acceptable for pathological inputs
        pass


@given(st.text(alphabet='0123456789-+(), ', min_size=1))
def test_default_parse_value_binop_as_string(s):
    """Test that binary operations are returned as strings, not evaluated."""
    assume('-' in s or '+' in s)
    # Construct something that looks like a binop
    assume(any(c.isdigit() for c in s))
    
    # Skip if it's actually a valid literal
    try:
        ast.literal_eval(s)
        assume(False)  # Skip valid literals
    except (ValueError, SyntaxError):
        pass
    
    # Check for patterns like "1+2" or "2017-10-10"
    if any(op in s for op in ['+', '-']) and sum(c.isdigit() for c in s) >= 2:
        # Split by operators to check if we have digits on both sides
        for op in ['+', '-']:
            if op in s:
                parts = s.split(op)
                if len(parts) >= 2:
                    left = parts[0].strip()
                    right = op.join(parts[1:]).strip()
                    if left and right and any(c.isdigit() for c in left) and any(c.isdigit() for c in right):
                        # This looks like a binop
                        result = parser.DefaultParseValue(s)
                        # Property: BinOps should be returned as strings
                        assert isinstance(result, str)
                        assert result == s
                        return