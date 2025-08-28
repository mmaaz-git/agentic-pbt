import os
import tempfile
import types
from unittest.mock import Mock

import pytest
from hypothesis import assume, given, settings, strategies as st

# Import the modules to test
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.parse import Variables
from jurigged.utils import EventSource, glob_filter, or_filter, shift_lineno


# Test 1: Variables.free property invariant
@given(
    assigned=st.sets(st.text(min_size=1, max_size=10)),
    read=st.sets(st.text(min_size=1, max_size=10))
)
def test_variables_free_invariant(assigned, read):
    """Test that Variables.free equals read - assigned as documented"""
    v = Variables(assigned=assigned, read=read)
    assert v.free == read - assigned


# Test 2: Variables.__or__ combines sets correctly
@given(
    assigned1=st.sets(st.text(min_size=1, max_size=10)),
    read1=st.sets(st.text(min_size=1, max_size=10)),
    assigned2=st.sets(st.text(min_size=1, max_size=10)),
    read2=st.sets(st.text(min_size=1, max_size=10))
)
def test_variables_or_operation(assigned1, read1, assigned2, read2):
    """Test that __or__ combines Variables correctly"""
    v1 = Variables(assigned=assigned1, read=read1)
    v2 = Variables(assigned=assigned2, read=read2)
    result = v1 | v2
    
    assert result.assigned == assigned1 | assigned2
    assert result.read == read1 | read2
    # Also check the free property is consistent
    assert result.free == (read1 | read2) - (assigned1 | assigned2)


# Test 3: EventSource emission calls all listeners
@given(
    num_listeners=st.integers(min_value=0, max_value=10),
    args=st.lists(st.integers(), min_size=0, max_size=3),
    kwargs=st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), min_size=0, max_size=3)
)
def test_eventsource_emission(num_listeners, args, kwargs):
    """Test that EventSource.emit calls all registered listeners"""
    es = EventSource()
    called_listeners = []
    
    for i in range(num_listeners):
        mock = Mock()
        mock.side_effect = lambda *a, **k: called_listeners.append(i)
        es.register(mock)
    
    es.emit(*args, **kwargs)
    
    # Check all listeners were called exactly once in order
    assert called_listeners == list(range(num_listeners))
    
    # Check they were called with correct arguments
    for listener in es:
        listener.assert_called_once_with(*args, **kwargs)


# Test 4: EventSource history functionality
@given(
    initial_events=st.lists(
        st.tuples(
            st.lists(st.integers(), min_size=0, max_size=2),
            st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), min_size=0, max_size=2)
        ),
        min_size=0,
        max_size=5
    )
)
def test_eventsource_history(initial_events):
    """Test that EventSource with save_history applies history to new listeners"""
    es = EventSource(save_history=True)
    
    # Emit initial events
    for args, kwargs in initial_events:
        es.emit(*args, **kwargs)
    
    # Register a new listener
    received_events = []
    def listener(*args, **kwargs):
        received_events.append((args, kwargs))
    
    es.register(listener, apply_history=True)
    
    # Check that listener received all historical events
    assert received_events == [(tuple(args), kwargs) for args, kwargs in initial_events]


# Test 5: glob_filter directory handling
@given(
    dirname=st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '*' not in x)
)
def test_glob_filter_directory_appends_star(dirname):
    """Test that glob_filter appends * to directory paths"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test directory
        test_dir = os.path.join(tmpdir, dirname)
        os.makedirs(test_dir, exist_ok=True)
        
        # Create the filter
        matcher = glob_filter(test_dir)
        
        # Create a file in the directory
        test_file = os.path.join(test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # The matcher should match files in the directory
        assert matcher(test_file) == True
        
        # It should not match the directory itself
        assert matcher(test_dir) == False


# Test 6: or_filter logic property
@given(
    patterns=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5),
    test_string=st.text(min_size=1, max_size=20)
)
def test_or_filter_logic(patterns, test_string):
    """Test that or_filter returns true if any filter matches"""
    # Create filters that check if test_string contains pattern
    filters = [lambda s, p=p: p in s for p in patterns]
    
    combined = or_filter(filters)
    
    # The combined filter should return true if any pattern is in test_string
    expected = any(p in test_string for p in patterns)
    assert combined(test_string) == expected


# Test 7: shift_lineno recursive property
@given(
    delta=st.integers(min_value=-100, max_value=100),
    initial_lineno=st.integers(min_value=1, max_value=1000)
)
def test_shift_lineno_code_object(delta, initial_lineno):
    """Test that shift_lineno correctly shifts line numbers in code objects"""
    # Create a simple code object
    code_str = """
def test_func():
    pass
"""
    
    # Compile to get a code object
    compiled = compile(code_str, '<test>', 'exec')
    
    # Find the nested function code object
    for const in compiled.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == 'test_func':
            func_code = const
            break
    else:
        # No nested function found, skip test
        assume(False)
    
    # Apply shift_lineno
    shifted = shift_lineno(func_code, delta)
    
    # Check that the line number was shifted
    assert shifted.co_firstlineno == func_code.co_firstlineno + delta
    
    # Check that nested constants are also shifted
    for orig_const, shifted_const in zip(func_code.co_consts, shifted.co_consts):
        if isinstance(orig_const, types.CodeType):
            assert isinstance(shifted_const, types.CodeType)
            assert shifted_const.co_firstlineno == orig_const.co_firstlineno + delta


# Test 8: shift_lineno preserves non-code constants
@given(
    delta=st.integers(min_value=-100, max_value=100),
    non_code_consts=st.lists(
        st.one_of(st.none(), st.integers(), st.text(), st.floats(allow_nan=False)),
        min_size=0,
        max_size=5
    )
)
def test_shift_lineno_preserves_non_code(delta, non_code_consts):
    """Test that shift_lineno preserves non-code constants unchanged"""
    for const in non_code_consts:
        result = shift_lineno(const, delta)
        assert result == const  # Non-code objects should be returned unchanged