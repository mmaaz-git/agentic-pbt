from hypothesis import given, strategies as st, settings
from click.globals import get_current_context, _local, push_context, pop_context
from click.core import Context, Command
import pytest


@given(st.text(min_size=1))
@settings(max_examples=1000)
def test_string_stack_returns_last_char(test_string):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    # Set stack to a string
    _local.stack = test_string
    
    # get_current_context should raise RuntimeError for non-list stack
    # But it actually returns the last character for strings
    result = get_current_context(silent=False)
    
    # This demonstrates the bug: it returns the last character
    assert result == test_string[-1]
    
    # Clean up
    _local.stack = []


# Minimal reproduction
def test_minimal_reproduction():
    # Clear context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    # Set stack to string
    _local.stack = "hello"
    
    # This should raise RuntimeError but returns 'o' instead
    result = get_current_context(silent=False)
    assert result == 'o'
    
    # Clean up
    _local.stack = []