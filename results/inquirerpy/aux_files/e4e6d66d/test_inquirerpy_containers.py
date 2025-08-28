#!/usr/bin/env python3
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import pytest
from unittest.mock import Mock, MagicMock
from InquirerPy.containers.spinner import SPINNERS, SpinnerWindow
from InquirerPy.containers.instruction import InstructionWindow
from InquirerPy.containers.message import MessageWindow
from InquirerPy.containers.validation import ValidationWindow, ValidationFloat
from prompt_toolkit.filters import Condition


# Test 1: SPINNERS namedtuple invariants
def test_spinners_invariants():
    """All SPINNERS patterns should be non-empty lists of strings"""
    # SPINNERS is actually a class with class attributes, not a namedtuple instance
    pattern_names = [name for name in dir(SPINNERS) if not name.startswith('_') and not callable(getattr(SPINNERS, name))]
    for name in pattern_names:
        pattern = getattr(SPINNERS, name)
        assert isinstance(pattern, list), f"SPINNERS.{name} should be a list"
        assert len(pattern) > 0, f"SPINNERS.{name} should not be empty"
        for item in pattern:
            assert isinstance(item, str), f"All items in SPINNERS.{name} should be strings"
            assert len(item) > 0, f"Items in SPINNERS.{name} should not be empty strings"


# Test 2: SpinnerWindow initialization with various inputs
@given(
    delay=st.floats(min_value=0.001, max_value=10.0),
    text=st.text(min_size=0, max_size=1000),
)
def test_spinner_window_init(delay, text):
    """SpinnerWindow should initialize without crashing with valid inputs"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    # Test with default pattern
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        delay=delay,
        text=text
    )
    assert spinner._delay == delay
    assert spinner._text == text or "Loading ..."
    assert spinner._pattern == SPINNERS.line  # default
    assert spinner._char == spinner._pattern[0]
    assert spinner._spinning == False


# Test 3: SpinnerWindow pattern preservation
@given(
    pattern=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20)
)
def test_spinner_window_pattern_preservation(pattern):
    """SpinnerWindow should preserve the pattern passed to it"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=pattern
    )
    assert spinner._pattern == pattern
    assert spinner._char == pattern[0]


# Test 4: SpinnerWindow with SPINNERS patterns
@given(pattern_name=st.sampled_from([name for name in dir(SPINNERS) if not name.startswith('_') and not callable(getattr(SPINNERS, name))]))
def test_spinner_window_with_spinners_patterns(pattern_name):
    """SpinnerWindow should work with all predefined SPINNERS patterns"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    pattern = getattr(SPINNERS, pattern_name)
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=pattern
    )
    assert spinner._pattern == pattern
    assert spinner._char == pattern[0]
    
    # Test _get_text returns proper format
    text = spinner._get_text()
    assert isinstance(text, list)
    assert len(text) == 3
    assert text[0][0] == "class:spinner_pattern"
    assert text[0][1] == pattern[0]
    assert text[1] == ("", " ")
    assert text[2][0] == "class:spinner_text"


# Test 5: SpinnerWindow start() idempotence
@pytest.mark.asyncio
async def test_spinner_start_idempotence():
    """Multiple calls to start() should not create multiple concurrent spinners"""
    loading_state = [True, False]
    loading_filter = Condition(lambda: loading_state.pop(0) if loading_state else False)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b", "c"],
        delay=0.001
    )
    
    assert spinner._spinning == False
    
    # Start spinner
    task1 = asyncio.create_task(spinner.start())
    await asyncio.sleep(0.0001)  # Let it start
    
    # Try to start again while running - should return immediately
    assert spinner._spinning == True
    task2 = asyncio.create_task(spinner.start())
    
    # Wait for both to complete
    await task1
    await task2
    
    assert spinner._spinning == False


# Test 6: InstructionWindow initialization
@given(
    message=st.text(min_size=0, max_size=1000),
)
def test_instruction_window_init(message):
    """InstructionWindow should initialize without crashing"""
    filter_cond = Condition(lambda: True)
    
    window = InstructionWindow(message=message, filter=filter_cond)
    assert window._message == message
    
    # Test _get_message returns proper format
    formatted = window._get_message()
    assert formatted == [("class:long_instruction", message)]


# Test 7: MessageWindow initialization
@given(
    wrap_lines=st.booleans(),
    show_cursor=st.booleans(),
)
def test_message_window_init(wrap_lines, show_cursor):
    """MessageWindow should initialize without crashing"""
    filter_cond = Condition(lambda: True)
    message = [("", "test message")]
    
    window = MessageWindow(
        message=message,
        filter=filter_cond,
        wrap_lines=wrap_lines,
        show_cursor=show_cursor
    )
    # Just check it doesn't crash - implementation details are prompt_toolkit's responsibility


# Test 8: ValidationWindow and ValidationFloat initialization
@given(
    left=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    right=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    bottom=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
    top=st.one_of(st.none(), st.integers(min_value=0, max_value=100)),
)
def test_validation_windows_init(left, right, bottom, top):
    """ValidationWindow and ValidationFloat should initialize without crashing"""
    filter_cond = Condition(lambda: True)
    message = [("class:error", "Invalid input")]
    
    # Test ValidationWindow
    val_window = ValidationWindow(invalid_message=message, filter=filter_cond)
    
    # Test ValidationFloat
    val_float = ValidationFloat(
        invalid_message=message,
        filter=filter_cond,
        left=left,
        right=right,
        bottom=bottom,
        top=top
    )
    # Just check they don't crash


# Test 9: Edge case - empty pattern list
def test_spinner_empty_pattern():
    """SpinnerWindow should handle empty pattern gracefully or fail predictably"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    # This should either use default or raise an error
    try:
        spinner = SpinnerWindow(
            loading=loading_filter,
            redraw=redraw,
            pattern=[]
        )
        # If it doesn't raise, it should use default
        assert spinner._pattern == SPINNERS.line
    except (IndexError, ValueError):
        # Empty pattern causing an error is acceptable behavior
        pass


# Test 10: SpinnerWindow with None pattern uses default
def test_spinner_none_pattern():
    """SpinnerWindow with None pattern should use default"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=None
    )
    assert spinner._pattern == SPINNERS.line
    assert spinner._char == SPINNERS.line[0]


if __name__ == "__main__":
    # Run basic tests
    test_spinners_invariants()
    test_spinner_none_pattern()
    print("Basic tests passed!")
    
    # Run property tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])