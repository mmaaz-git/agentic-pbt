"""Advanced property-based tests for fire.trace module to find bugs."""

import shlex
from hypothesis import assume, given, strategies as st, settings, HealthCheck
import fire.trace


@given(
    st.lists(
        st.tuples(
            st.booleans(),  # has_error
            st.booleans(),  # capacity
        ),
        min_size=1,
        max_size=20
    )
)
def test_get_last_healthy_element_edge_cases(elements_data):
    """Test GetLastHealthyElement with all-error traces."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Remove the initial element to test edge case
    trace.elements = []
    
    for i, (has_error, capacity) in enumerate(elements_data):
        if has_error:
            element = fire.trace.FireTraceElement(
                component=None, 
                action="error", 
                target=f"func{i}", 
                error=Exception("test")
            )
        else:
            element = fire.trace.FireTraceElement(
                component=object(), 
                action="called", 
                target=f"func{i}",
                capacity=capacity
            )
        trace.elements.append(element)
    
    # This should handle the case where there are no elements
    last_healthy = trace.GetLastHealthyElement()
    
    # Check if it handles empty trace properly
    assert last_healthy is not None


@given(
    st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=127))
    .filter(lambda s: '\x00' not in s)  # Null bytes break shlex
)
def test_quote_with_control_characters(text):
    """Test _Quote with ASCII control characters."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Special case for --flag=value
    if text.startswith('--') and '=' in text:
        quoted = trace._Quote(text)
        prefix, value = text.split('=', 1)
        expected = shlex.quote(prefix) + '=' + shlex.quote(value)
        assert quoted == expected
    else:
        quoted = trace._Quote(text)
        assert quoted == shlex.quote(text)


@given(
    st.lists(
        st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cf"])),
        min_size=1
    )
)
def test_get_command_roundtrip(args):
    """Test if GetCommand output can be used to recreate similar trace."""
    trace = fire.trace.FireTrace(initial_component=object(), name="mycmd")
    
    # Add components with args
    trace.AddCalledComponent(
        component=object(),
        target="func",
        args=args,
        filename=None,
        lineno=None,
        capacity=False
    )
    
    command = trace.GetCommand(include_separators=False)
    
    # Parse the command
    try:
        parsed = shlex.split(command)
        
        # Should start with the name
        assert parsed[0] == "mycmd"
        
        # Rest should be the args (including empty strings)
        # This reveals the issue: empty strings are included
        expected_args = ["mycmd"] + args
        assert parsed == expected_args
    except ValueError:
        # Command couldn't be parsed - this is a bug
        assert False, f"Command '{command}' couldn't be parsed"


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=10),
    st.booleans()
)
def test_add_separator_behavior(args, use_separator):
    """Test AddSeparator functionality."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test", separator='--')
    
    # Add component
    trace.AddCalledComponent(
        component=object(),
        target="func",
        args=args,
        filename=None,
        lineno=None,
        capacity=True  # Has capacity for more args
    )
    
    if use_separator:
        trace.AddSeparator()
    
    command = trace.GetCommand(include_separators=True)
    
    # Check if separator is included correctly
    if use_separator:
        assert '--' in command
    
    # NeedsSeparator should return False if separator was added
    if use_separator:
        assert not trace.NeedsSeparator()


@given(
    st.text(min_size=1).filter(lambda s: '=' in s)
)
def test_quote_equals_edge_cases(text):
    """Test _Quote with various equals sign positions."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    quoted = trace._Quote(text)
    
    # Check special handling for --flag=value
    if text.startswith('--') and '=' in text:
        # Should split at first = only
        prefix, value = text.split('=', 1)
        expected = shlex.quote(prefix) + '=' + shlex.quote(value)
        assert quoted == expected
    else:
        # Regular quoting
        assert quoted == shlex.quote(text)
    
    # Result should always be parseable
    parsed = shlex.split(quoted)
    assert len(parsed) == 1
    assert parsed[0] == text


@given(
    st.lists(
        st.one_of(
            st.none(),  # None component
            st.just(object()),  # Object component
            st.text(),  # String component
            st.integers(),  # Integer component
            st.floats(allow_nan=False, allow_infinity=False),  # Float component
        ),
        min_size=1,
        max_size=10
    )
)
def test_various_component_types(components):
    """Test trace with various component types."""
    trace = fire.trace.FireTrace(initial_component=components[0], name="test")
    
    for i, component in enumerate(components[1:]):
        trace.AddCalledComponent(
            component=component,
            target=f"func{i}",
            args=[str(i)],
            filename=None,
            lineno=None,
            capacity=False
        )
    
    # GetResult should return the last component
    result = trace.GetResult()
    if len(components) > 1:
        assert result == components[-1]
    else:
        assert result == components[0]


@given(
    st.lists(st.text(), min_size=0, max_size=10),
    st.text()
)
def test_add_error_behavior(args, error_msg):
    """Test AddError method."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Add an error
    error = ValueError(error_msg)
    trace.AddError(error, args)
    
    # Should have error
    assert trace.HasError()
    
    # Last element should be an error
    last_element = trace.elements[-1]
    assert last_element.HasError()
    assert last_element.args == args
    
    # GetCommand should skip error elements
    command = trace.GetCommand()
    # Error args should not appear in command
    for arg in args:
        if arg:  # Only non-empty args would appear
            assert arg not in command