#!/usr/bin/env python3
"""Advanced property-based tests for jurigged.utils module to find edge cases."""

import os
import sys
import tempfile
import types
from pathlib import Path

# Add the jurigged env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import jurigged.utils as utils


# Advanced EventSource tests
@given(
    save_history=st.booleans(),
    num_listeners=st.integers(min_value=0, max_value=20),
    num_events=st.integers(min_value=0, max_value=50)
)
@settings(max_examples=500)
def test_eventsource_listener_modification_during_emit(save_history, num_listeners, num_events):
    """Test EventSource behavior when listeners modify the list during emit."""
    source = utils.EventSource(save_history=save_history)
    
    call_log = []
    
    # Create listeners that might add or remove other listeners
    for i in range(num_listeners):
        def make_listener(idx):
            def listener(*args, **kwargs):
                call_log.append(('call', idx, args, kwargs))
                # Sometimes add a new listener during emit
                if idx % 3 == 0:
                    def new_listener(*a, **k):
                        call_log.append(('new', idx, a, k))
                    source.append(new_listener)
            return listener
        source.register(make_listener(i))
    
    # Emit events and see what happens
    for event_id in range(num_events):
        initial_listener_count = len(source)
        source.emit(event_id)
        
        # Count how many calls happened for this event
        event_calls = [entry for entry in call_log if len(entry) > 2 and entry[2] == (event_id,)]
        
        # Original listeners should all be called
        original_calls = [entry for entry in event_calls if entry[0] == 'call']
        assert len(original_calls) >= min(num_listeners, initial_listener_count)


@given(
    save_history=st.booleans(),
    event_data=st.lists(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.lists(st.integers(), max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=3)
        ),
        min_size=0,
        max_size=10
    )
)
def test_eventsource_complex_data_types(save_history, event_data):
    """Test EventSource with various data types."""
    source = utils.EventSource(save_history=save_history)
    
    received = []
    
    def listener(*args, **kwargs):
        received.append(args)
    
    source.register(listener)
    
    # Emit each piece of data
    for data in event_data:
        source.emit(data)
    
    # Should receive all data
    assert len(received) == len(event_data)
    for i, data in enumerate(event_data):
        assert received[i] == (data,)


# Advanced glob_filter tests
@given(
    base_path=st.text(min_size=1, max_size=10).filter(lambda x: x.isprintable() and '/' not in x and '\\' not in x and '\x00' not in x),
    pattern_suffix=st.sampled_from(['*', '*.txt', '*.py', '**/*.py', '**/test_*.py'])
)
def test_glob_filter_common_patterns(base_path, pattern_suffix):
    """Test glob_filter with common glob patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a directory structure
        base_dir = os.path.join(tmpdir, base_path)
        os.makedirs(base_dir, exist_ok=True)
        
        # Create some test files
        test_files = [
            os.path.join(base_dir, 'file.txt'),
            os.path.join(base_dir, 'script.py'),
            os.path.join(base_dir, 'test_something.py'),
        ]
        
        for filepath in test_files:
            Path(filepath).touch()
        
        # Create subdirectory with files
        sub_dir = os.path.join(base_dir, 'subdir')
        os.makedirs(sub_dir, exist_ok=True)
        sub_files = [
            os.path.join(sub_dir, 'nested.py'),
            os.path.join(sub_dir, 'test_nested.py'),
        ]
        for filepath in sub_files:
            Path(filepath).touch()
        
        # Test the pattern
        pattern = os.path.join(base_dir, pattern_suffix)
        matcher = utils.glob_filter(pattern)
        
        # The matcher should be callable
        assert callable(matcher)
        
        # Test against all files
        all_files = test_files + sub_files
        matches = [f for f in all_files if matcher(f)]
        
        # Verify the behavior makes sense for the pattern
        if pattern_suffix == '*':
            # Should match files in base_dir only
            assert any(matcher(f) for f in test_files)
        elif pattern_suffix == '*.txt':
            # Should match .txt files
            assert matcher(test_files[0])  # file.txt
            assert not matcher(test_files[1])  # script.py
        elif pattern_suffix == '*.py':
            # Should match .py files in base_dir
            assert not matcher(test_files[0])  # file.txt
            assert matcher(test_files[1])  # script.py
            assert matcher(test_files[2])  # test_something.py


@given(
    path_components=st.lists(
        st.text(min_size=1, max_size=10).filter(
            lambda x: x.isprintable() and '/' not in x and '\\' not in x and '\x00' not in x and x != '.' and x != '..'
        ),
        min_size=1,
        max_size=5
    )
)
def test_glob_filter_absolute_vs_relative(path_components):
    """Test glob_filter handling of absolute vs relative paths."""
    # Build a relative path
    rel_path = os.path.join(*path_components)
    
    # Get matcher for relative path
    matcher = utils.glob_filter(rel_path)
    
    # The pattern should have been converted to absolute
    # Test by checking if it matches the absolute version
    abs_path = os.path.abspath(rel_path)
    
    # Create a test file path
    test_file = os.path.join(abs_path, "test.txt") if os.path.isabs(abs_path) else os.path.join(os.path.abspath(rel_path), "test.txt")
    
    # The matcher should work with absolute paths
    result = matcher(test_file)
    assert isinstance(result, bool)


# Advanced or_filter tests
@given(
    num_filters=st.integers(min_value=0, max_value=10),
    test_value=st.integers(min_value=-100, max_value=100)
)
def test_or_filter_empty_list(num_filters, test_value):
    """Test or_filter with edge cases including empty list."""
    if num_filters == 0:
        # What happens with empty list?
        filters = []
        try:
            combined = utils.or_filter(filters)
            # If it doesn't raise an error, test the behavior
            result = combined(test_value)
            # With no filters, what should it return?
            assert isinstance(result, bool)
        except (IndexError, ValueError, TypeError) as e:
            # Empty list might cause an error
            pass
    else:
        # Normal case
        filters = [lambda x, i=i: x > i*10 for i in range(num_filters)]
        combined = utils.or_filter(filters)
        result = combined(test_value)
        expected = any(test_value > i*10 for i in range(num_filters))
        assert result == expected


@given(
    filters_results=st.lists(st.booleans(), min_size=1, max_size=10)
)
def test_or_filter_all_combinations(filters_results):
    """Test or_filter with all possible boolean combinations."""
    # Create filters that return the specified results
    filters = [lambda x, result=r: result for r in filters_results]
    
    combined = utils.or_filter(filters)
    
    # Test with any input (doesn't matter since our filters ignore it)
    result = combined("test")
    
    # Should return True if any filter returns True
    expected = any(filters_results)
    assert result == expected


# Advanced shift_lineno tests
@given(
    delta=st.integers(min_value=-1000, max_value=1000),
    num_nested_functions=st.integers(min_value=0, max_value=3)
)
def test_shift_lineno_deeply_nested(delta, num_nested_functions):
    """Test shift_lineno with deeply nested functions."""
    # Build nested function dynamically
    func_str = "def f0(): pass"
    for i in range(1, num_nested_functions + 1):
        indent = "  " * i
        func_str = f"def f{i}():\n{indent}{func_str}"
    
    # Compile and get code object
    try:
        code = compile(func_str, "<test>", "exec")
    except:
        # Skip if compilation fails
        assume(False)
    
    # Shift line numbers
    shifted = utils.shift_lineno(code, delta)
    
    # Verify the shift
    assert isinstance(shifted, types.CodeType)
    assert shifted.co_firstlineno == code.co_firstlineno + delta


@given(
    original_lineno=st.integers(min_value=1, max_value=100000),
    delta=st.integers()
)
@example(original_lineno=1, delta=-10)  # Test negative result
@example(original_lineno=2**31-100, delta=200)  # Test overflow
def test_shift_lineno_boundary_values(original_lineno, delta):
    """Test shift_lineno with boundary values."""
    # Create a simple function at a specific line
    def test_func():
        pass
    
    # Manually create a code object with specific line number
    original_code = test_func.__code__
    modified_code = original_code.replace(co_firstlineno=original_lineno)
    
    # Shift the line numbers
    shifted_code = utils.shift_lineno(modified_code, delta)
    
    # Check the result
    expected_lineno = original_lineno + delta
    
    # Line numbers might have limits or wrap around
    if expected_lineno < 0:
        # What happens with negative line numbers?
        pass  # Implementation-dependent
    
    assert isinstance(shifted_code, types.CodeType)
    assert shifted_code.co_firstlineno == expected_lineno


@given(
    const_values=st.lists(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=20),
            st.binary(max_size=20)
        ),
        max_size=5
    ),
    delta=st.integers(min_value=-100, max_value=100)
)
def test_shift_lineno_preserves_non_code_constants(const_values, delta):
    """Test that shift_lineno preserves non-code constants exactly."""
    # Create a function with various constants
    def test_func():
        return const_values
    
    original_code = test_func.__code__
    
    # Shift line numbers
    shifted_code = utils.shift_lineno(original_code, delta)
    
    # Non-code constants should be preserved exactly
    for i, const in enumerate(original_code.co_consts):
        if not isinstance(const, types.CodeType):
            # Should be the exact same object or value
            shifted_const = shifted_code.co_consts[i]
            if const is None or isinstance(const, (bool, int, float, str, bytes)):
                assert shifted_const == const
            else:
                assert shifted_const is const


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])