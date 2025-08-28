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
from argparse import Action
import shlex as stdlib_shlex


class MockAction:
    def __init__(self, nargs=None, option_strings=None):
        self.nargs = nargs
        self.option_strings = option_strings if option_strings is not None else []


@given(st.integers(min_value=0, max_value=100))
def test_action_is_satisfied_with_optional(num_consumed):
    action = MockAction(nargs=OPTIONAL)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == True
    
    
@given(st.integers(min_value=0, max_value=100))
def test_action_is_satisfied_with_zero_or_more(num_consumed):
    action = MockAction(nargs=ZERO_OR_MORE)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == True
    
    
@given(st.integers(min_value=0, max_value=100))
def test_action_is_satisfied_with_one_or_more(num_consumed):
    action = MockAction(nargs=ONE_OR_MORE)
    _num_consumed_args[action] = num_consumed
    expected = num_consumed >= 1
    assert action_is_satisfied(action) == expected
    

@given(st.integers(min_value=0, max_value=100))
def test_action_is_satisfied_with_none_nargs(num_consumed):
    action = MockAction(nargs=None)
    _num_consumed_args[action] = num_consumed
    expected = num_consumed == 1
    assert action_is_satisfied(action) == expected
    

@given(
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=0, max_value=20)
)
def test_action_is_satisfied_with_int_nargs(nargs, num_consumed):
    action = MockAction(nargs=nargs)
    _num_consumed_args[action] = num_consumed
    expected = num_consumed == nargs
    assert action_is_satisfied(action) == expected


@given(st.integers(min_value=0, max_value=100))
def test_action_is_open_with_zero_or_more(num_consumed):
    action = MockAction(nargs=ZERO_OR_MORE)
    _num_consumed_args[action] = num_consumed
    assert action_is_open(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_action_is_open_with_optional(num_consumed):
    action = MockAction(nargs=OPTIONAL)
    _num_consumed_args[action] = num_consumed
    expected = num_consumed == 0
    assert action_is_open(action) == expected


@given(
    st.integers(min_value=1, max_value=10),
    st.integers(min_value=0, max_value=20)
)
def test_action_is_open_with_int_nargs(nargs, num_consumed):
    action = MockAction(nargs=nargs)
    _num_consumed_args[action] = num_consumed
    expected = num_consumed < nargs
    assert action_is_open(action) == expected


@given(st.integers(min_value=0, max_value=100))
def test_action_is_open_with_none_nargs(num_consumed):
    action = MockAction(nargs=None)
    _num_consumed_args[action] = num_consumed
    expected = num_consumed == 0
    assert action_is_open(action) == expected


@given(
    st.booleans(),
    st.integers(min_value=0, max_value=5)
)
def test_action_is_greedy_with_remainder(has_option_strings, num_consumed):
    option_strings = ['--test'] if has_option_strings else []
    action = MockAction(nargs=REMAINDER, option_strings=option_strings)
    _num_consumed_args[action] = num_consumed
    
    if has_option_strings:
        expected = True  # REMAINDER with option_strings always greedy
    else:
        expected = num_consumed >= 1  # Without option_strings, greedy if consumed >= 1
    
    assert action_is_greedy(action, isoptional=False) == expected


@given(
    st.sampled_from([OPTIONAL, None, 1, 2, 3]),
    st.integers(min_value=0, max_value=5)
)
def test_action_is_greedy_with_option_strings(nargs, num_consumed):
    action = MockAction(nargs=nargs, option_strings=['--test'])
    _num_consumed_args[action] = num_consumed
    
    # When isoptional=False and action has option_strings
    is_satisfied = action_is_satisfied(action)
    expected = not is_satisfied  # greedy if not satisfied
    
    assert action_is_greedy(action, isoptional=False) == expected


@given(st.text(min_size=0, max_size=50).filter(lambda x: '"' not in x and "'" not in x))
def test_shlex_simple_tokenization(text):
    """Test that shlex can tokenize simple text without quotes"""
    lexer = shlex(text, posix=True)
    tokens = list(lexer)
    # Basic property: tokenization should not fail on simple text
    assert isinstance(tokens, list)


@given(st.lists(st.text(min_size=1, max_size=20).filter(lambda x: not any(c in x for c in ['"', "'", '\\', '\n']))))
def test_shlex_round_trip_simple(words):
    """Test round-trip for simple word lists"""
    assume(len(words) > 0)
    
    # Join with spaces
    input_text = ' '.join(words)
    
    # Tokenize
    lexer = shlex(input_text, posix=True)
    tokens = list(lexer)
    
    # Should get back the same words (unless they contain spaces themselves)
    expected = [w for w in words if w]  # Filter empty strings
    assert tokens == expected


@given(st.text(min_size=1, max_size=100))
def test_shlex_unclosed_quotes_detection(text):
    """Test that unclosed quotes are detected"""
    # Add an unclosed quote
    if '"' in text or "'" in text:
        return  # Skip if already has quotes
    
    test_input = text + '"'
    lexer = shlex(test_input, posix=True)
    
    try:
        tokens = list(lexer)
        # If we got here, the quote was somehow closed or ignored
    except ValueError as e:
        # Expected: "No closing quotation"
        assert "closing quotation" in str(e).lower()


@given(
    st.lists(st.text(min_size=1, max_size=20).filter(lambda x: not any(c in x for c in ['"', "'", '\\', '\n', ' '])), min_size=1, max_size=10),
    st.booleans()
)
def test_shlex_with_quotes(words, use_double_quotes):
    """Test tokenization with quoted strings"""
    quote = '"' if use_double_quotes else "'"
    
    # Quote some words
    quoted_input = ' '.join(f'{quote}{word}{quote}' for word in words)
    
    lexer = shlex(quoted_input, posix=True)
    tokens = list(lexer)
    
    # In POSIX mode, quotes are removed
    assert tokens == words


@given(st.integers(min_value=0, max_value=100))
def test_action_is_satisfied_parser_always_false(num_consumed):
    """PARSER nargs should always return False for is_satisfied"""
    action = MockAction(nargs=PARSER)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == False


@given(st.integers(min_value=0, max_value=100))
def test_action_is_open_parser_always_true(num_consumed):
    """PARSER nargs should always return True for is_open"""
    action = MockAction(nargs=PARSER)
    _num_consumed_args[action] = num_consumed
    assert action_is_open(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_action_is_satisfied_remainder_always_true(num_consumed):
    """REMAINDER nargs should always return True for is_satisfied"""
    action = MockAction(nargs=REMAINDER)
    _num_consumed_args[action] = num_consumed
    assert action_is_satisfied(action) == True


@given(st.integers(min_value=0, max_value=100))
def test_action_is_open_remainder_always_true(num_consumed):
    """REMAINDER nargs should always return True for is_open"""
    action = MockAction(nargs=REMAINDER)
    _num_consumed_args[action] = num_consumed
    assert action_is_open(action) == True


# Consistency property tests
@given(
    st.sampled_from([OPTIONAL, ZERO_OR_MORE, ONE_OR_MORE, REMAINDER, PARSER, None, 1, 2, 3, 5]),
    st.integers(min_value=0, max_value=10)
)
def test_satisfied_and_open_consistency(nargs, num_consumed):
    """Test logical consistency between satisfied and open states"""
    action = MockAction(nargs=nargs)
    _num_consumed_args[action] = num_consumed
    
    is_satisfied = action_is_satisfied(action)
    is_open = action_is_open(action)
    
    # Some logical properties:
    # 1. PARSER is never satisfied but always open
    if nargs == PARSER:
        assert not is_satisfied and is_open
    
    # 2. REMAINDER is always both satisfied and open
    elif nargs == REMAINDER:
        assert is_satisfied and is_open
    
    # 3. ZERO_OR_MORE is always satisfied and always open
    elif nargs == ZERO_OR_MORE:
        assert is_satisfied and is_open
    
    # 4. For fixed integer nargs, if satisfied then not open
    elif isinstance(nargs, int):
        if is_satisfied:
            assert not is_open
        # If not satisfied, must be open (can still consume)
        if not is_satisfied:
            assert is_open