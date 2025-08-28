#!/usr/bin/env python3
"""Test to confirm the bug in SpinnerWindow exception handling"""
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

import pytest
from unittest.mock import Mock
from InquirerPy.containers.spinner import SpinnerWindow
from prompt_toolkit.filters import Condition


@pytest.mark.asyncio
async def test_spinner_exception_leaves_spinning_true():
    """
    BUG: If redraw() raises an exception during spinner execution,
    the _spinning flag remains True, preventing future start() calls.
    """
    # Setup a filter that returns True twice then False
    call_count = [0]
    def loading_check():
        call_count[0] += 1
        return call_count[0] <= 2
    
    loading_filter = Condition(loading_check)
    
    # Create a redraw that raises an exception
    redraw = Mock()
    redraw.side_effect = Exception("Redraw failed!")
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b", "c"],
        delay=0.001
    )
    
    # Initially _spinning should be False
    assert spinner._spinning == False
    
    # Try to start the spinner (will raise exception)
    with pytest.raises(Exception) as exc_info:
        await spinner.start()
    assert str(exc_info.value) == "Redraw failed!"
    
    # BUG: _spinning remains True after exception!
    print(f"After exception, _spinning = {spinner._spinning}")
    assert spinner._spinning == True, "This is the bug - _spinning should be False after exception"
    
    # This means subsequent calls to start() will return immediately without doing anything
    # because of the check on line 100-101 of spinner.py
    
    # Try to start again with working redraw
    spinner._redraw = Mock()  # Replace with working redraw
    
    # Reset the loading filter
    call_count[0] = 0
    
    # This call will return immediately without starting because _spinning is still True
    await spinner.start()
    
    # The new redraw was never called because start() returned early
    assert spinner._redraw.call_count == 0, "Redraw not called because _spinning was stuck at True"
    
    print("\nBUG CONFIRMED: SpinnerWindow._spinning remains True after exception in start()")
    print("This prevents the spinner from being restarted after an error occurs.")


@pytest.mark.asyncio
async def test_correct_behavior_without_exception():
    """Control test: Normal execution correctly sets _spinning to False"""
    call_count = [0]
    def loading_check():
        call_count[0] += 1
        return call_count[0] <= 2
    
    loading_filter = Condition(loading_check)
    redraw = Mock()  # Normal mock that doesn't raise
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b"],
        delay=0.001
    )
    
    assert spinner._spinning == False
    await spinner.start()
    assert spinner._spinning == False  # Correctly reset after normal completion
    
    # Can start again successfully
    call_count[0] = 0
    await spinner.start()
    assert redraw.call_count > 0  # Redraw was called


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])