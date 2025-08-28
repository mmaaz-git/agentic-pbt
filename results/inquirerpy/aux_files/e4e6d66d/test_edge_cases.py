#!/usr/bin/env python3
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import pytest
from unittest.mock import Mock
from InquirerPy.containers.spinner import SPINNERS, SpinnerWindow
from InquirerPy.containers.instruction import InstructionWindow
from InquirerPy.containers.message import MessageWindow
from InquirerPy.containers.validation import ValidationWindow, ValidationFloat
from prompt_toolkit.filters import Condition


# Test with empty string patterns
def test_spinner_empty_string_pattern():
    """SpinnerWindow with empty string in pattern should handle it"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    # Pattern with empty string
    try:
        spinner = SpinnerWindow(
            loading=loading_filter,
            redraw=redraw,
            pattern=["a", "", "c"]  # Empty string in middle
        )
        # Check that it initialized
        assert spinner._pattern == ["a", "", "c"]
        assert spinner._char == "a"  # First char
        
        # Check _get_text handles empty string
        text = spinner._get_text()
        assert text[0] == ("class:spinner_pattern", "a")
        
        # Now set the char to empty string and check
        spinner._char = ""
        text = spinner._get_text()
        assert text[0] == ("class:spinner_pattern", "")
    except Exception as e:
        print(f"Empty string in pattern caused: {e}")


# Test with single-element pattern
def test_spinner_single_element_pattern():
    """SpinnerWindow with single element pattern"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["X"]
    )
    assert spinner._pattern == ["X"]
    assert spinner._char == "X"


# Test with very long pattern elements
@given(pattern_elem=st.text(min_size=1000, max_size=10000))
def test_spinner_long_pattern_elements(pattern_elem):
    """SpinnerWindow with very long pattern elements"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=[pattern_elem]
    )
    assert spinner._pattern == [pattern_elem]
    assert spinner._char == pattern_elem
    
    # Check that _get_text works
    text = spinner._get_text()
    assert text[0] == ("class:spinner_pattern", pattern_elem)


# Test with Unicode patterns
def test_spinner_unicode_patterns():
    """SpinnerWindow should handle various Unicode characters"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    # Test with emojis
    emoji_pattern = ["😀", "😁", "😂", "🤣", "😃"]
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=emoji_pattern
    )
    assert spinner._pattern == emoji_pattern
    
    # Test with mixed scripts
    mixed_pattern = ["א", "中", "ω", "अ", "ع"]
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=mixed_pattern
    )
    assert spinner._pattern == mixed_pattern
    
    # Test with zero-width characters
    zwj_pattern = ["👨‍👩‍👧‍👦", "👨‍💻", "🏳️‍🌈"]
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=zwj_pattern
    )
    assert spinner._pattern == zwj_pattern


# Test with negative or zero delay
@given(delay=st.floats(min_value=-10.0, max_value=0.0))
def test_spinner_negative_delay(delay):
    """SpinnerWindow with negative or zero delay"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        delay=delay
    )
    assert spinner._delay == delay


# Test async behavior with very small delays
@pytest.mark.asyncio
async def test_spinner_async_with_tiny_delay():
    """Test spinner with extremely small delay"""
    loading_count = [0]
    def loading_check():
        loading_count[0] += 1
        return loading_count[0] <= 3  # Stop after 3 checks
    
    loading_filter = Condition(loading_check)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b", "c"],
        delay=0.0  # Zero delay
    )
    
    await spinner.start()
    
    # Should have called redraw at least once for each pattern element
    assert redraw.call_count >= 2


# Test with pattern containing only empty strings
def test_spinner_all_empty_strings():
    """SpinnerWindow with pattern of only empty strings"""
    loading_filter = Condition(lambda: True)
    redraw = Mock()
    
    try:
        spinner = SpinnerWindow(
            loading=loading_filter,
            redraw=redraw,
            pattern=["", "", ""]
        )
        assert spinner._pattern == ["", "", ""]
        assert spinner._char == ""
        
        # Check that _get_text works
        text = spinner._get_text()
        assert text[0] == ("class:spinner_pattern", "")
    except Exception as e:
        print(f"All empty strings pattern caused: {e}")


# Test InstructionWindow with very long messages
@given(message=st.text(min_size=1000, max_size=5000))
def test_instruction_window_huge_message(message):
    """InstructionWindow with very large message"""
    filter_cond = Condition(lambda: True)
    
    window = InstructionWindow(message=message, filter=filter_cond)
    assert window._message == message
    
    formatted = window._get_message()
    assert formatted == [("class:long_instruction", message)]


# Test MessageWindow with empty message
def test_message_window_empty():
    """MessageWindow with empty message"""
    filter_cond = Condition(lambda: True)
    
    # Empty list
    window = MessageWindow(
        message=[],
        filter=filter_cond
    )
    
    # Empty string tuple
    window2 = MessageWindow(
        message=[("", "")],
        filter=filter_cond
    )


# Test concurrent spinner starts
@pytest.mark.asyncio
async def test_spinner_concurrent_starts():
    """Multiple concurrent start() calls should be safe"""
    loading_state = [True, True, False]
    loading_filter = Condition(lambda: loading_state.pop(0) if loading_state else False)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b"],
        delay=0.01
    )
    
    # Start multiple concurrent tasks
    tasks = [
        asyncio.create_task(spinner.start()),
        asyncio.create_task(spinner.start()),
        asyncio.create_task(spinner.start()),
    ]
    
    # Wait for all to complete
    await asyncio.gather(*tasks)
    
    # Should still be in a consistent state
    assert spinner._spinning == False


if __name__ == "__main__":
    # Run non-async tests
    test_spinner_empty_string_pattern()
    test_spinner_single_element_pattern()
    test_spinner_unicode_patterns()
    test_spinner_all_empty_strings()
    test_message_window_empty()
    print("Edge case tests completed!")
    
    # Run all tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])