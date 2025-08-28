import sys
import os
import types
from hypothesis import given, strategies as st, assume, settings
import pytest
import math

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.utils import EventSource, glob_filter, or_filter, shift_lineno
from jurigged.codetools import attrproxy


# Test EventSource properties
@given(
    save_history=st.booleans(),
    num_listeners=st.integers(min_value=0, max_value=10),
    num_emissions=st.integers(min_value=0, max_value=10),
    args=st.lists(st.integers(), min_size=0, max_size=5)
)
def test_eventsource_all_listeners_called(save_history, num_listeners, num_emissions, args):
    """All registered listeners should be called on each emit"""
    source = EventSource(save_history=save_history)
    call_counts = []
    
    for i in range(num_listeners):
        counter = [0]
        call_counts.append(counter)
        
        def listener(*a, counter=counter, **kw):
            counter[0] += 1
        
        source.register(listener, apply_history=False)
    
    for _ in range(num_emissions):
        source.emit(*args)
    
    # All listeners should have been called exactly num_emissions times
    for counter in call_counts:
        assert counter[0] == num_emissions


@given(
    num_pre_emissions=st.integers(min_value=0, max_value=10),
    num_post_emissions=st.integers(min_value=0, max_value=10)
)
def test_eventsource_history_replay(num_pre_emissions, num_post_emissions):
    """When save_history=True, new listeners should receive history"""
    source = EventSource(save_history=True)
    
    # Emit some events before registering listener
    for i in range(num_pre_emissions):
        source.emit(i)
    
    # Register listener with history replay
    calls = []
    source.register(lambda x: calls.append(x), apply_history=True)
    
    # Should have received all historical events
    assert len(calls) == num_pre_emissions
    assert calls == list(range(num_pre_emissions))
    
    # Emit more events
    for i in range(num_post_emissions):
        source.emit(i + num_pre_emissions)
    
    # Should have all events
    expected = list(range(num_pre_emissions + num_post_emissions))
    assert calls == expected


# Test glob_filter properties
@given(
    dirname=st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '*' not in x),
    filename=st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '*' not in x)
)
def test_glob_filter_directory_pattern(dirname, filename):
    """Directory patterns should match files in that directory"""
    # Create a test path
    test_path = f"/tmp/{dirname}/{filename}"
    
    # Directory pattern should match files in that directory
    pattern = f"/tmp/{dirname}"
    matcher = glob_filter(pattern)
    
    # The glob_filter adds /* to directory patterns
    # So it should match files in the directory
    assert matcher(test_path) == True


@given(
    pattern=st.text(min_size=1).filter(lambda x: not x.startswith('~') and not x.startswith('/'))
)
def test_glob_filter_relative_to_absolute(pattern):
    """Relative patterns should be converted to absolute"""
    matcher = glob_filter(pattern)
    
    # The pattern should have been converted to absolute
    # We can't test the exact path, but we can verify it's callable
    assert callable(matcher)
    
    # Test that it can be called without error
    result = matcher("/some/test/path")
    assert isinstance(result, bool)


# Test or_filter properties
@given(
    num_filters=st.integers(min_value=1, max_value=10),
    test_input=st.text(min_size=1, max_size=100),
    match_indices=st.lists(st.integers(min_value=0), min_size=0)
)
def test_or_filter_logical_or(num_filters, test_input, match_indices):
    """or_filter should return True if any filter matches"""
    filters = []
    
    for i in range(num_filters):
        if i in match_indices:
            # This filter should match
            filters.append(lambda x, i=i: True)
        else:
            # This filter should not match
            filters.append(lambda x, i=i: False)
    
    if not filters:
        return
        
    matcher = or_filter(filters)
    result = matcher(test_input)
    
    # Should be True if any filter matched
    expected = any(i < num_filters for i in match_indices)
    assert result == expected


@given(st.text(min_size=1, max_size=100))
def test_or_filter_single_optimization(test_input):
    """Single filter optimization should behave identically"""
    # Create a simple filter
    def single_filter(x):
        return len(x) > 50
    
    # or_filter with single filter should return the filter itself
    matcher = or_filter([single_filter])
    
    # Should behave identically to the original filter
    assert matcher(test_input) == single_filter(test_input)


# Test shift_lineno properties
def create_simple_code():
    """Create a simple code object for testing"""
    code_str = """
def test():
    pass
"""
    return compile(code_str, "test.py", "exec")


@given(delta=st.integers(min_value=-100, max_value=100))
def test_shift_lineno_round_trip(delta):
    """Shifting by delta then -delta should give original line numbers"""
    original = create_simple_code()
    
    # Shift forward
    shifted = shift_lineno(original, delta)
    
    # Shift back
    restored = shift_lineno(shifted, -delta)
    
    # Line numbers should be restored
    assert restored.co_firstlineno == original.co_firstlineno


@given(
    delta1=st.integers(min_value=-50, max_value=50),
    delta2=st.integers(min_value=-50, max_value=50)
)
def test_shift_lineno_associative(delta1, delta2):
    """Shifting by delta1 then delta2 should equal shifting by delta1+delta2"""
    original = create_simple_code()
    
    # Shift in two steps
    step1 = shift_lineno(original, delta1)
    step2 = shift_lineno(step1, delta2)
    
    # Shift in one step
    combined = shift_lineno(original, delta1 + delta2)
    
    # Should have same result
    assert step2.co_firstlineno == combined.co_firstlineno


# Test attrproxy properties
class TestClass:
    pass


@given(
    attr_name=st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier() and not x.startswith('_')),
    value=st.one_of(st.integers(), st.text(), st.floats(allow_nan=False, allow_infinity=False))
)
def test_attrproxy_get_set_equivalence(attr_name, value):
    """Getting/setting through proxy should equal direct access"""
    obj = TestClass()
    proxy = attrproxy(obj)
    
    # Set through proxy
    proxy[attr_name] = value
    
    # Get directly should match
    assert getattr(obj, attr_name) == value
    
    # Get through proxy should match
    assert proxy[attr_name] == value
    
    # Set directly
    new_value = "modified_" + str(value)
    setattr(obj, attr_name, new_value)
    
    # Get through proxy should reflect change
    assert proxy[attr_name] == new_value


@given(
    attr_name=st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier() and not x.startswith('_'))
)
def test_attrproxy_missing_attribute(attr_name):
    """Missing attributes should raise KeyError when accessed via []"""
    obj = TestClass()
    proxy = attrproxy(obj)
    
    # Ensure attribute doesn't exist
    if hasattr(obj, attr_name):
        delattr(obj, attr_name)
    
    # Should raise KeyError
    with pytest.raises(KeyError):
        _ = proxy[attr_name]
    
    # get() with default should work
    default = "default_value"
    assert proxy.get(attr_name, default) == default


if __name__ == "__main__":
    # Run with increased examples for better coverage
    settings.register_profile("thorough", max_examples=1000)
    settings.load_profile("thorough")
    
    pytest.main([__file__, "-v"])