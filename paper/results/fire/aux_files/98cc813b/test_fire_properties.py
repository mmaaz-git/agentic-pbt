import json
import fire.parser as parser
from hypothesis import given, strategies as st, assume, settings


# Property 1: SeparateFlagArgs invariant
# The concatenation of the two output lists (with '--' restored) should match the input
@given(st.lists(st.text(min_size=1).filter(lambda x: '\x00' not in x)))
def test_separateflagargs_invariant(args):
    fire_args, flag_args = parser.SeparateFlagArgs(args)
    
    # The function splits on '--', so let's verify the invariant
    assert isinstance(fire_args, list)
    assert isinstance(flag_args, list)
    
    # If there was a '--' separator, the total length should be maintained
    if '--' in args:
        # Find the last '--' position
        separator_indices = [i for i, arg in enumerate(args) if arg == '--']
        if separator_indices:
            last_sep = separator_indices[-1]
            # Everything before last '--' should be in fire_args
            # Everything after should be in flag_args
            expected_fire = args[:last_sep]
            expected_flag = args[last_sep + 1:]
            assert fire_args == expected_fire
            assert flag_args == expected_flag
    else:
        # Without '--', all args should be fire_args
        assert fire_args == args
        assert flag_args == []


# Property 2: DefaultParseValue round-trip for JSON-serializable values
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.lists(st.integers(), max_size=5),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=3)
))
def test_defaultparsevalue_roundtrip(value):
    # Convert to string representation
    if isinstance(value, bool):
        str_value = str(value)
    else:
        str_value = json.dumps(value)
    
    # Parse and check
    parsed = parser.DefaultParseValue(str_value)
    
    # For simple types, parsing should recover the original value
    if isinstance(value, (int, float, list, dict)):
        assert parsed == value
    elif isinstance(value, bool):
        # Note: Fire treats 'True' and 'False' specially
        assert parsed == value


# Property 3: DefaultParseValue idempotence for strings
@given(st.text(min_size=1).filter(lambda x: not any(c in x for c in ['(', ')', '[', ']', '{', '}', '"', "'", '\\'])))
def test_defaultparsevalue_string_idempotence(text):
    # For plain strings without special characters, parsing should be idempotent
    parsed_once = parser.DefaultParseValue(text)
    
    # If it was parsed as a string, parsing again should give the same result
    if isinstance(parsed_once, str):
        parsed_twice = parser.DefaultParseValue(parsed_once)
        assert parsed_once == parsed_twice


# Property 4: DefaultParseValue preserves Python literals
@given(st.text())
def test_defaultparsevalue_literal_detection(text):
    try:
        # If text is a valid Python literal, DefaultParseValue should parse it as such
        import ast
        expected = ast.literal_eval(text)
        parsed = parser.DefaultParseValue(text)
        
        # Fire's parser should match Python's literal_eval for valid literals
        assert parsed == expected
    except (ValueError, SyntaxError):
        # Not a valid literal, so it should be treated as a string
        parsed = parser.DefaultParseValue(text)
        # Strings with no special chars should remain strings
        if not any(c in text for c in ['(', ')', '[', ']', '{', '}', '"', "'", '\\']):
            assert isinstance(parsed, str)


# Property 5: SeparateFlagArgs length preservation
@given(st.lists(st.text(min_size=1)))
def test_separateflagargs_length_preservation(args):
    fire_args, flag_args = parser.SeparateFlagArgs(args)
    
    # Count of '--' separators
    separator_count = args.count('--')
    
    # Total elements should be preserved (minus the separator)
    if separator_count > 0:
        assert len(fire_args) + len(flag_args) == len(args) - 1
    else:
        assert len(fire_args) + len(flag_args) == len(args)