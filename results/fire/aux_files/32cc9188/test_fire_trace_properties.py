#!/usr/bin/env python3
"""Property-based tests for fire.trace module using Hypothesis."""

import fire.trace as trace
from hypothesis import given, strategies as st, assume, settings
import string


# Strategy for generating valid component names/values
component_strategy = st.one_of(
    st.text(min_size=1, max_size=100),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
)

# Strategy for generating valid target names
target_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_", 
    min_size=1, 
    max_size=50
)

# Strategy for generating filenames
filename_strategy = st.text(min_size=1, max_size=100).map(lambda s: s + ".py")

# Strategy for generating line numbers
lineno_strategy = st.integers(min_value=1, max_value=10000)

# Strategy for generating args tuples
args_strategy = st.tuples(
    st.text(min_size=0, max_size=50),
    st.text(min_size=0, max_size=50)
)


@given(
    initial=component_strategy,
    components=st.lists(component_strategy, min_size=1, max_size=10),
    targets=st.lists(target_strategy, min_size=1, max_size=10),
    filenames=st.lists(filename_strategy, min_size=1, max_size=10),
    linenos=st.lists(lineno_strategy, min_size=1, max_size=10)
)
def test_get_result_returns_last_component(initial, components, targets, filenames, linenos):
    """GetResult() should always return the component from the last element added."""
    # Ensure lists have same length
    min_len = min(len(components), len(targets), len(filenames), len(linenos))
    components = components[:min_len]
    targets = targets[:min_len]
    filenames = filenames[:min_len]
    linenos = linenos[:min_len]
    
    t = trace.FireTrace(initial)
    
    # Initially should return initial component
    assert t.GetResult() == initial
    
    # Add components and verify GetResult() tracks the last one
    for component, target, filename, lineno in zip(components, targets, filenames, linenos):
        t.AddAccessedProperty(component, target, None, filename, lineno)
        # GetResult should now return the last component added
        assert t.GetResult() == component


@given(
    initial=component_strategy,
    error_message=st.text(min_size=1, max_size=100),
    error_args=st.lists(st.text(max_size=50), min_size=0, max_size=5)
)
def test_has_error_state_consistency(initial, error_message, error_args):
    """HasError() should be false initially and true only after AddError()."""
    t = trace.FireTrace(initial)
    
    # Initially should have no error
    assert t.HasError() is False
    
    # Add some operations without errors
    t.AddAccessedProperty("component", "target", None, "file.py", 10)
    assert t.HasError() is False
    
    # Add an error
    error = ValueError(error_message)
    t.AddError(error, error_args)
    
    # Now should have error
    assert t.HasError() is True
    
    # Adding more operations shouldn't change error state
    t.AddAccessedProperty("another", "target2", None, "file2.py", 20)
    assert t.HasError() is True


@given(
    initial=component_strategy,
    args_list=st.lists(
        st.tuples(
            st.text(alphabet=string.printable, min_size=0, max_size=20),
            st.text(alphabet=string.printable, min_size=0, max_size=20)
        ),
        min_size=1,
        max_size=5
    ),
    targets=st.lists(target_strategy, min_size=1, max_size=5),
    filenames=st.lists(filename_strategy, min_size=1, max_size=5),
    linenos=st.lists(lineno_strategy, min_size=1, max_size=5)
)
def test_get_command_concatenation(initial, args_list, targets, filenames, linenos):
    """GetCommand() should correctly concatenate arguments from trace elements."""
    # Ensure all lists have same length
    min_len = min(len(args_list), len(targets), len(filenames), len(linenos))
    args_list = args_list[:min_len]
    targets = targets[:min_len]
    filenames = filenames[:min_len]
    linenos = linenos[:min_len]
    
    t = trace.FireTrace(initial)
    
    expected_parts = []
    
    for args, target, filename, lineno in zip(args_list, targets, filenames, linenos):
        t.AddCalledComponent(
            "result", target, args, filename, lineno, False,
            action=trace.CALLED_ROUTINE
        )
        # Based on the test, args are joined with space
        if args:
            expected_parts.extend(args)
    
    command = t.GetCommand(include_separators=False)
    
    # The command should contain all the arguments
    for part in expected_parts:
        if part:  # Skip empty strings
            assert part in command


@given(
    component=component_strategy,
    action=st.text(min_size=1, max_size=100),
    target=st.one_of(st.none(), target_strategy),
    filename=st.one_of(st.none(), filename_strategy),
    lineno=st.one_of(st.none(), lineno_strategy)
)
def test_fire_trace_element_string_representation(component, action, target, filename, lineno):
    """FireTraceElement string representation should match its action when no target."""
    el = trace.FireTraceElement(
        component=component,
        action=action,
        target=target,
        filename=filename,
        lineno=lineno
    )
    
    el_str = str(el)
    
    # Based on the test, when there's no target/filename/lineno, str should be just the action
    if target is None and filename is None and lineno is None:
        assert el_str == action
    else:
        # With metadata, the string should contain the action
        assert action in el_str


@given(
    initial=component_strategy,
    num_operations=st.integers(min_value=0, max_value=20)
)
@settings(max_examples=100)
def test_trace_length_consistency(initial, num_operations):
    """The number of elements in trace should match operations performed."""
    t = trace.FireTrace(initial)
    
    # Initial trace has one element (the initial component)
    assert len(t.elements) == 1
    
    # Add operations
    for i in range(num_operations):
        t.AddAccessedProperty(f"comp_{i}", f"target_{i}", None, "file.py", i+1)
    
    # Should have initial element plus all added operations
    assert len(t.elements) == 1 + num_operations


@given(
    component=component_strategy,
    action=st.text(min_size=1, max_size=100),
    capacity=st.one_of(st.none(), st.booleans())
)
def test_element_has_capacity(component, action, capacity):
    """FireTraceElement.HasCapacity() should return its capacity value."""
    el = trace.FireTraceElement(
        component=component,
        action=action,
        capacity=capacity
    )
    
    # HasCapacity should return the capacity value
    assert el.HasCapacity() == capacity


@given(
    initial=component_strategy,
    separator=st.text(alphabet=string.punctuation, min_size=1, max_size=3)
)
def test_fire_trace_separator_property(initial, separator):
    """FireTrace separator should be stored and used correctly."""
    t = trace.FireTrace(initial, separator=separator)
    
    # The separator should be stored
    assert t.separator == separator
    
    # Add a separator to an element
    t.AddSeparator()
    
    # Last element should have the separator
    last_element = t.elements[-1] if t.elements else None
    if last_element:
        assert last_element.HasSeparator()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])