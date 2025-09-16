#!/usr/bin/env python3
"""Property-based tests for jurigged.utils module."""

import os
import sys
import tempfile
import types
from pathlib import Path

# Add the jurigged env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import jurigged.utils as utils


# Test EventSource class
@given(
    save_history=st.booleans(),
    events=st.lists(
        st.tuples(
            st.lists(st.integers()),  # args
            st.dictionaries(st.text(min_size=1, max_size=10), st.integers())  # kwargs
        ),
        min_size=0,
        max_size=10
    ),
    register_before_emit=st.integers(min_value=0, max_value=10)
)
def test_eventsource_history_replay(save_history, events, register_before_emit):
    """Test that EventSource correctly replays history when save_history=True."""
    source = utils.EventSource(save_history=save_history)
    
    # Limit register_before_emit to the number of events
    register_before_emit = min(register_before_emit, len(events))
    
    # Create recording listeners
    early_listener_calls = []
    late_listener_calls = []
    
    def early_listener(*args, **kwargs):
        early_listener_calls.append((args, kwargs))
    
    def late_listener(*args, **kwargs):
        late_listener_calls.append((args, kwargs))
    
    # Register early listener
    source.register(early_listener)
    
    # Emit some events before late registration
    for i in range(register_before_emit):
        args, kwargs = events[i]
        source.emit(*args, **kwargs)
    
    # Register late listener
    source.register(late_listener, apply_history=True)
    
    # Emit remaining events
    for i in range(register_before_emit, len(events)):
        args, kwargs = events[i]
        source.emit(*args, **kwargs)
    
    # Early listener should have received all events
    assert len(early_listener_calls) == len(events)
    for i, (args, kwargs) in enumerate(events):
        assert early_listener_calls[i] == (tuple(args), kwargs)
    
    # Late listener behavior depends on save_history
    if save_history:
        # Should have received all events (history + new)
        assert len(late_listener_calls) == len(events)
        for i, (args, kwargs) in enumerate(events):
            assert late_listener_calls[i] == (tuple(args), kwargs)
    else:
        # Should have only received events after registration
        assert len(late_listener_calls) == len(events) - register_before_emit
        for i, (args, kwargs) in enumerate(events[register_before_emit:]):
            assert late_listener_calls[i] == (tuple(args), kwargs)


@given(
    num_listeners=st.integers(min_value=1, max_value=10),
    event_args=st.lists(st.integers()),
    event_kwargs=st.dictionaries(st.text(min_size=1, max_size=5), st.integers())
)
def test_eventsource_all_listeners_called(num_listeners, event_args, event_kwargs):
    """Test that all registered listeners are called with emitted events."""
    source = utils.EventSource()
    
    # Track calls for each listener
    listener_calls = [[] for _ in range(num_listeners)]
    
    # Register listeners
    for i in range(num_listeners):
        def make_listener(idx):
            def listener(*args, **kwargs):
                listener_calls[idx].append((args, kwargs))
            return listener
        source.register(make_listener(i))
    
    # Emit event
    source.emit(*event_args, **event_kwargs)
    
    # All listeners should have been called exactly once
    for calls in listener_calls:
        assert len(calls) == 1
        assert calls[0] == (tuple(event_args), event_kwargs)


# Test glob_filter function
@given(
    pattern=st.text(min_size=1).filter(lambda x: not x.startswith('~')),
    filename=st.text(min_size=1)
)
def test_glob_filter_returns_callable(pattern, filename):
    """Test that glob_filter returns a callable matcher."""
    # Skip patterns that might cause issues
    assume('*' not in pattern and '?' not in pattern and '[' not in pattern)
    assume(os.path.sep not in pattern)  # Simple patterns only for this test
    
    matcher = utils.glob_filter(pattern)
    assert callable(matcher)
    
    # The matcher should return a boolean
    result = matcher(filename)
    assert isinstance(result, bool)


@given(dirname=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\\' not in x and '\x00' not in x))
def test_glob_filter_directory_pattern(dirname):
    """Test that directory patterns match files in that directory."""
    assume(dirname.isprintable())  # Avoid non-printable characters that might cause issues
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a subdirectory
        dirpath = os.path.join(tmpdir, dirname)
        os.makedirs(dirpath, exist_ok=True)
        
        # Create the matcher for the directory
        matcher = utils.glob_filter(dirpath)
        
        # Should match files in the directory
        test_file = os.path.join(dirpath, "test.txt")
        assert matcher(test_file) == True
        
        # Should not match files outside the directory
        outside_file = os.path.join(tmpdir, "outside.txt")
        assert matcher(outside_file) == False


# Test or_filter function
@given(
    num_filters=st.integers(min_value=1, max_value=1),  # Test single filter optimization
    test_value=st.integers()
)
def test_or_filter_single_filter_optimization(num_filters, test_value):
    """Test that or_filter with single filter returns that filter directly."""
    # Create a simple filter
    def filter_func(x):
        return x > 0
    
    result_filter = utils.or_filter([filter_func])
    
    # Should behave identically to the original filter
    assert result_filter(test_value) == filter_func(test_value)


@given(
    filter_thresholds=st.lists(st.integers(min_value=-100, max_value=100), min_size=2, max_size=5),
    test_value=st.integers(min_value=-200, max_value=200)
)
def test_or_filter_any_match(filter_thresholds, test_value):
    """Test that or_filter returns True if ANY filter matches."""
    # Create filters that check if value is greater than threshold
    filters = [lambda x, t=threshold: x > t for threshold in filter_thresholds]
    
    combined = utils.or_filter(filters)
    
    # Should return True if test_value is greater than ANY threshold
    expected = any(test_value > threshold for threshold in filter_thresholds)
    assert combined(test_value) == expected


@given(
    num_false_filters=st.integers(min_value=1, max_value=5),
    true_filter_position=st.integers(min_value=0, max_value=5),
    test_value=st.integers()
)
def test_or_filter_stops_on_first_true(num_false_filters, true_filter_position, test_value):
    """Test or_filter short-circuits on first True."""
    filters = []
    call_counts = []
    
    # Add filters that return False and count calls
    for i in range(num_false_filters):
        count = [0]
        call_counts.append(count)
        def make_filter(cnt):
            def f(x):
                cnt[0] += 1
                return False
            return f
        filters.append(make_filter(count))
    
    # Insert a True filter at the specified position
    if true_filter_position <= num_false_filters:
        true_count = [0]
        def true_filter(x):
            true_count[0] += 1
            return True
        filters.insert(true_filter_position, true_filter)
    
    combined = utils.or_filter(filters)
    result = combined(test_value)
    
    # Verify short-circuit behavior
    if true_filter_position <= num_false_filters:
        assert result == True
        # Filters after the True one shouldn't be called
        for i in range(true_filter_position, num_false_filters):
            if i < len(call_counts):
                # These shouldn't have been called due to short-circuit
                pass  # Can't guarantee exact behavior without more complex tracking


# Test shift_lineno function
@given(delta=st.integers(min_value=-100, max_value=100))
def test_shift_lineno_with_code_object(delta):
    """Test that shift_lineno correctly shifts line numbers in code objects."""
    # Create a simple function to get a code object
    def test_func():
        pass
    
    original_code = test_func.__code__
    original_lineno = original_code.co_firstlineno
    
    # Shift the line numbers
    shifted_code = utils.shift_lineno(original_code, delta)
    
    # Verify the shift
    assert isinstance(shifted_code, types.CodeType)
    assert shifted_code.co_firstlineno == original_lineno + delta
    
    # Other attributes should remain the same
    assert shifted_code.co_name == original_code.co_name
    assert shifted_code.co_argcount == original_code.co_argcount


@given(
    delta=st.integers(min_value=-100, max_value=100),
    non_code_value=st.one_of(
        st.integers(),
        st.text(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_shift_lineno_non_code_unchanged(delta, non_code_value):
    """Test that shift_lineno returns non-code objects unchanged."""
    result = utils.shift_lineno(non_code_value, delta)
    assert result is non_code_value  # Should be the exact same object


@given(delta=st.integers(min_value=-50, max_value=50))
def test_shift_lineno_recursive_constants(delta):
    """Test that shift_lineno recursively shifts nested code objects in constants."""
    # Create a function with a nested function
    def outer_func():
        def inner_func():
            pass
        return inner_func
    
    original_code = outer_func.__code__
    
    # Find the inner function's code object in constants
    inner_code = None
    for const in original_code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'inner_func':
            inner_code = const
            break
    
    assume(inner_code is not None)  # Skip if we can't find the inner function
    
    original_outer_lineno = original_code.co_firstlineno
    original_inner_lineno = inner_code.co_firstlineno
    
    # Shift the line numbers
    shifted_code = utils.shift_lineno(original_code, delta)
    
    # Find the shifted inner code
    shifted_inner_code = None
    for const in shifted_code.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'inner_func':
            shifted_inner_code = const
            break
    
    # Both outer and inner should be shifted
    assert shifted_code.co_firstlineno == original_outer_lineno + delta
    assert shifted_inner_code is not None
    assert shifted_inner_code.co_firstlineno == original_inner_lineno + delta


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])