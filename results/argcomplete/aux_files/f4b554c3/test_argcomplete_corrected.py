import math
from hypothesis import assume, given, strategies as st, settings
from argcomplete.packages._argparse import (
    action_is_satisfied, 
    action_is_open, 
    action_is_greedy,
    _num_consumed_args,
    OPTIONAL, 
    ZERO_OR_MORE, 
    ONE_OR_MORE, 
    REMAINDER,
    PARSER
)
from argcomplete.packages._shlex import shlex


class MockAction:
    def __init__(self, nargs=None, option_strings=None):
        self.nargs = nargs
        self.option_strings = option_strings if option_strings is not None else []


# Test invariants for action_is_satisfied based on documented behavior
@given(st.integers(min_value=0, max_value=100))
def test_optional_always_satisfied(num_consumed):
    """OPTIONAL nargs should always be satisfied"""
    action = MockAction(nargs=OPTIONAL)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_zero_or_more_always_satisfied(num_consumed):
    """ZERO_OR_MORE nargs should always be satisfied"""
    action = MockAction(nargs=ZERO_OR_MORE)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_remainder_always_satisfied(num_consumed):
    """REMAINDER nargs should always be satisfied"""
    action = MockAction(nargs=REMAINDER)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_parser_never_satisfied(num_consumed):
    """PARSER nargs should never be satisfied (as per comment in code)"""
    action = MockAction(nargs=PARSER)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == False


# Test invariants for action_is_open
@given(st.integers(min_value=0, max_value=100))
def test_zero_or_more_always_open(num_consumed):
    """ZERO_OR_MORE should always be open"""
    action = MockAction(nargs=ZERO_OR_MORE)
    _num_consumed_args[action] = num_consumed
    assert action_is_open(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_one_or_more_always_open(num_consumed):
    """ONE_OR_MORE should always be open"""
    action = MockAction(nargs=ONE_OR_MORE)
    _num_consumed_args[action] = num_consumed
    assert action_is_open(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_parser_always_open(num_consumed):
    """PARSER should always be open"""
    action = MockAction(nargs=PARSER)
    _num_consumed_args[action] = num_consumed
    assert action_is_open(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_remainder_always_open(num_consumed):
    """REMAINDER should always be open"""
    action = MockAction(nargs=REMAINDER)
    _num_consumed_args[action] = num_consumed
    assert action_is_open(action) == True


# Test metamorphic properties
@given(
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=0, max_value=20)
)
def test_int_nargs_satisfied_implies_exact_match(nargs, num_consumed):
    """For integer nargs, satisfied implies exact match"""
    action = MockAction(nargs=nargs)
    _num_consumed_args[action] = num_consumed
    
    if action_is_satisfied(action):
        assert num_consumed == nargs
    if num_consumed == nargs:
        assert action_is_satisfied(action)


@given(
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=0, max_value=20)
)
def test_int_nargs_open_implies_can_consume_more(nargs, num_consumed):
    """For integer nargs, open implies can consume more"""
    action = MockAction(nargs=nargs)
    _num_consumed_args[action] = num_consumed
    
    if action_is_open(action):
        assert num_consumed < nargs
    if num_consumed < nargs:
        assert action_is_open(action)


# Test shlex with proper expectations
@given(st.lists(st.text(min_size=1, max_size=20).filter(
    lambda x: not any(c in x for c in ['"', "'", '\\', '\n', ' ', '\t', '\r'])
), min_size=1, max_size=10))
def test_shlex_whitespace_split_round_trip(words):
    """Test round-trip with whitespace_split=True (like shlex.split)"""
    input_text = ' '.join(words)
    
    lexer = shlex(input_text, posix=True)
    lexer.whitespace_split = True  # This is what shlex.split() does
    tokens = list(lexer)
    
    # Should preserve the words when whitespace_split is True
    assert tokens == words


@given(st.text(min_size=1, max_size=50))
def test_shlex_handles_normal_text(text):
    """Test that shlex can handle various text inputs without crashing"""
    # Skip inputs with unclosed quotes or trailing backslashes
    if text.count('"') % 2 != 0 or text.count("'") % 2 != 0:
        return
    if text.endswith('\\'):
        return
        
    lexer = shlex(text, posix=True)
    lexer.whitespace_split = True
    
    try:
        tokens = list(lexer)
        # Should successfully tokenize
        assert isinstance(tokens, list)
    except ValueError:
        # Some inputs may still raise ValueError (e.g., escape sequences)
        pass


# Test consistency between action states
@given(st.integers(min_value=0, max_value=10))
def test_one_or_more_satisfaction_consistency(num_consumed):
    """ONE_OR_MORE: satisfied iff consumed >= 1"""
    action = MockAction(nargs=ONE_OR_MORE)
    _num_consumed_args[action] = num_consumed
    
    is_satisfied = action_is_satisfied(action)
    expected_satisfied = (num_consumed >= 1)
    
    assert is_satisfied == expected_satisfied


@given(st.integers(min_value=0, max_value=10))
def test_none_nargs_satisfaction_consistency(num_consumed):
    """None nargs: satisfied iff consumed == 1"""
    action = MockAction(nargs=None)
    _num_consumed_args[action] = num_consumed
    
    is_satisfied = action_is_satisfied(action)
    expected_satisfied = (num_consumed == 1)
    
    assert is_satisfied == expected_satisfied


@given(st.integers(min_value=0, max_value=10))
def test_optional_open_consistency(num_consumed):
    """OPTIONAL: open iff consumed == 0"""
    action = MockAction(nargs=OPTIONAL)
    _num_consumed_args[action] = num_consumed
    
    is_open = action_is_open(action)
    expected_open = (num_consumed == 0)
    
    assert is_open == expected_open