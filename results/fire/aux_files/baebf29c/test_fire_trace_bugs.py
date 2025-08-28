"""Targeted tests to find actual bugs in fire.trace module."""

import shlex
from hypothesis import given, strategies as st, settings, HealthCheck, example
import fire.trace


@given(st.just([]))
def test_get_last_healthy_element_empty_trace(dummy):
    """Test GetLastHealthyElement with completely empty trace."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Remove all elements including initial
    trace.elements = []
    
    # This should not crash but will raise IndexError
    try:
        result = trace.GetLastHealthyElement()
        # If it doesn't crash, check what it returns
        assert result is not None
    except IndexError:
        # Bug found: GetLastHealthyElement crashes on empty trace
        assert False, "GetLastHealthyElement raises IndexError on empty trace"


@given(
    st.lists(st.just(True), min_size=1, max_size=5)  # All errors
)
def test_get_last_healthy_element_all_errors(all_errors):
    """Test GetLastHealthyElement when all elements after initial are errors."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Add only error elements
    for i in range(len(all_errors)):
        element = fire.trace.FireTraceElement(
            component=None,
            action="error",
            target=f"func{i}",
            error=Exception(f"error{i}")
        )
        trace.elements.append(element)
    
    # Should return the initial element (which is always healthy)
    result = trace.GetLastHealthyElement()
    assert result == trace.elements[0]  # Initial element
    assert not result.HasError()


@given(
    st.lists(
        st.text(alphabet=st.sampled_from(['a', 'b', '=', '-'])),
        min_size=1,
        max_size=3
    ).map(lambda parts: ''.join(parts))
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_quote_with_equals_combinations(text):
    """Test _Quote with various combinations including equals."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    quoted = trace._Quote(text)
    
    # The result should always be parseable
    try:
        parsed = shlex.split(quoted)
        assert len(parsed) == 1
        assert parsed[0] == text
    except ValueError as e:
        # This would be a bug in the quoting
        assert False, f"Failed to parse quoted '{quoted}' from '{text}': {e}"


# Test specific edge cases
def test_quote_edge_cases():
    """Test specific edge cases for _Quote method."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Test case 1: String with only equals
    result = trace._Quote("=")
    assert shlex.split(result) == ["="]
    
    # Test case 2: --= (starts with -- and has =)
    result = trace._Quote("--=")
    parsed = shlex.split(result)
    assert len(parsed) == 1
    assert parsed[0] == "--="
    
    # Test case 3: --=value (no key part)
    result = trace._Quote("--=value")
    parsed = shlex.split(result)
    assert len(parsed) == 1
    assert parsed[0] == "--=value"
    
    # Test case 4: Multiple equals --key=val=ue
    result = trace._Quote("--key=val=ue")
    expected = shlex.quote("--key") + "=" + shlex.quote("val=ue")
    assert result == expected
    parsed = shlex.split(result)
    assert parsed[0] == "--key=val=ue"


def test_empty_string_in_args():
    """Test that empty strings in args are preserved in GetCommand."""
    trace = fire.trace.FireTrace(initial_component=object(), name="mycmd")
    
    # Add component with empty string args
    trace.AddCalledComponent(
        component=object(),
        target="func",
        args=["", "arg1", "", "arg2", ""],
        filename=None,
        lineno=None,
        capacity=False
    )
    
    command = trace.GetCommand(include_separators=False)
    parsed = shlex.split(command)
    
    # Bug: Empty strings are included in the command
    # This may be unintended as empty CLI args are unusual
    assert parsed == ["mycmd", "", "arg1", "", "arg2", ""]
    
    # This is likely a bug - empty strings as CLI arguments are very unusual
    # Most CLI tools would not expect empty string arguments


def test_needs_separator_edge_case():
    """Test NeedsSeparator with various edge cases."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Case 1: Empty trace (only initial element)
    assert not trace.NeedsSeparator()  # Initial element, no capacity
    
    # Case 2: Add element with capacity
    trace.AddCalledComponent(
        component=object(),
        target="func",
        args=["arg"],
        filename=None,
        lineno=None,
        capacity=True
    )
    assert trace.NeedsSeparator()  # Has capacity, no separator
    
    # Case 3: Add separator
    trace.AddSeparator()
    assert not trace.NeedsSeparator()  # Has separator now
    
    # Case 4: Add error after separator
    trace.AddError(ValueError("test"), ["error_arg"])
    # Should still not need separator (last healthy has separator)
    assert not trace.NeedsSeparator()


def test_add_accessed_property():
    """Test AddAccessedProperty method."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Add an accessed property
    trace.AddAccessedProperty(
        component="value",
        target="property_name",
        args=["arg1"],
        filename="test.py",
        lineno=42
    )
    
    # Check the element was added correctly
    assert len(trace.elements) == 2  # Initial + added
    element = trace.elements[-1]
    assert element.component == "value"
    assert element._target == "property_name"
    assert element.args == ["arg1"]
    assert element._filename == "test.py"
    assert element._lineno == 42
    assert element._action == "Accessed property"  # Specific action for properties


def test_large_number_of_elements():
    """Test trace with a large number of elements."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Add many elements
    for i in range(1000):
        if i % 3 == 0:
            # Add error every third element
            trace.AddError(ValueError(f"error{i}"), [f"arg{i}"])
        else:
            trace.AddCalledComponent(
                component=f"component{i}",
                target=f"func{i}",
                args=[f"arg{i}"],
                filename=f"file{i}.py",
                lineno=i,
                capacity=(i % 2 == 0)
            )
    
    # Should handle large traces
    assert trace.HasError()
    result = trace.GetResult()
    command = trace.GetCommand()
    
    # Command should skip error elements
    assert "error" not in command
    
    # Result should be last non-error component
    assert result != trace.elements[-1].component  # Last is error
    assert "component" in str(result)