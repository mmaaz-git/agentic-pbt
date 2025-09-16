#!/usr/bin/env python3
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

import pytest
from unittest.mock import Mock, call
from InquirerPy.containers.spinner import SpinnerWindow
from prompt_toolkit.filters import Condition


@pytest.mark.asyncio
async def test_spinner_pattern_rotation_order():
    """Verify spinner rotates through pattern in correct order"""
    loading_state = []
    pattern = ["a", "b", "c", "d"]
    
    # Create a loading filter that stops after going through pattern twice
    def loading_check():
        return len(loading_state) < len(pattern) * 2
    
    loading_filter = Condition(loading_check)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=pattern,
        delay=0.001
    )
    
    # Capture the char state at each redraw
    def capture_state():
        loading_state.append(spinner._char)
    
    redraw.side_effect = capture_state
    
    await spinner.start()
    
    # Should have gone through pattern twice
    expected = pattern * 2
    assert loading_state[:len(expected)] == expected


@pytest.mark.asyncio
async def test_spinner_stops_when_filter_false():
    """Spinner should stop immediately when filter becomes false"""
    loading_active = [True]
    
    def loading_check():
        return loading_active[0]
    
    loading_filter = Condition(loading_check)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b", "c"],
        delay=0.01
    )
    
    # Start spinner
    task = asyncio.create_task(spinner.start())
    
    # Let it run for a bit
    await asyncio.sleep(0.02)
    
    # Stop the spinner
    loading_active[0] = False
    
    # Wait for task to complete
    await task
    
    # Spinner should be stopped
    assert spinner._spinning == False


@pytest.mark.asyncio
async def test_spinner_char_consistency():
    """The char displayed should always be from the pattern"""
    loading_count = [0]
    pattern = ["x", "y", "z"]
    
    def loading_check():
        loading_count[0] += 1
        return loading_count[0] <= 10
    
    loading_filter = Condition(loading_check)
    chars_seen = []
    
    def capture_char():
        chars_seen.append(spinner._char)
    
    redraw = Mock(side_effect=capture_char)
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=pattern,
        delay=0.001
    )
    
    await spinner.start()
    
    # All chars seen should be from the pattern
    for char in chars_seen:
        assert char in pattern


@pytest.mark.asyncio
async def test_spinner_redraw_count():
    """Redraw should be called approximately once per delay period"""
    loading_count = [0]
    num_iterations = 5
    
    def loading_check():
        loading_count[0] += 1
        return loading_count[0] <= num_iterations
    
    loading_filter = Condition(loading_check)
    redraw = Mock()
    
    delay = 0.01
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b"],
        delay=delay
    )
    
    await spinner.start()
    
    # Should have called redraw approximately num_iterations times
    # Allow some margin for timing
    assert redraw.call_count >= num_iterations - 2
    assert redraw.call_count <= num_iterations + 2


@pytest.mark.asyncio  
async def test_spinner_exception_handling():
    """Test what happens if redraw raises an exception"""
    loading_count = [0]
    
    def loading_check():
        loading_count[0] += 1
        return loading_count[0] <= 3
    
    loading_filter = Condition(loading_check)
    
    # Redraw that raises exception on second call
    redraw = Mock()
    redraw.side_effect = [None, Exception("Redraw failed"), None]
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b", "c"],
        delay=0.001
    )
    
    # This might raise or might not, depending on error handling
    try:
        await spinner.start()
    except Exception:
        # Exception propagated - this is one valid behavior
        pass
    
    # Check if spinner state is consistent
    # Even if exception occurred, spinning should be false after completion
    assert spinner._spinning == False


@pytest.mark.asyncio
async def test_spinner_filter_evaluation_timing():
    """Test that filter is evaluated at expected times"""
    evaluations = []
    
    def loading_check():
        evaluations.append(len(evaluations))
        return len(evaluations) <= 5
    
    loading_filter = Condition(loading_check)
    redraw = Mock()
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=redraw,
        pattern=["a", "b"],
        delay=0.005
    )
    
    await spinner.start()
    
    # Filter should be evaluated at least once (at start) and then periodically
    assert len(evaluations) >= 1
    
    # The evaluations should be sequential
    for i, val in enumerate(evaluations):
        assert val == i


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])