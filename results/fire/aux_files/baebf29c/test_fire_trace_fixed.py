"""Property-based tests for fire.trace module - Fixed version."""

import shlex
from hypothesis import assume, given, strategies as st, settings, HealthCheck
import fire.trace


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1),  # target
            st.lists(st.text()),  # args
            st.booleans(),  # has_error
            st.booleans(),  # capacity
        ),
        min_size=1,
    )
)
def test_get_last_healthy_element_invariant(elements_data):
    """GetLastHealthyElement should always return a non-error element if any exist."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    has_healthy = False
    for target, args, has_error, capacity in elements_data:
        if has_error:
            element = fire.trace.FireTraceElement(
                component=None, action="error", target=target, args=args, error=Exception("test")
            )
        else:
            has_healthy = True
            element = fire.trace.FireTraceElement(
                component=object(), action="called", target=target, args=args, capacity=capacity
            )
        trace.elements.append(element)
    
    last_healthy = trace.GetLastHealthyElement()
    
    # Property: GetLastHealthyElement should never return an element with an error
    assert not last_healthy.HasError()
    
    # Property: If we have any healthy elements, the result should be one of them
    if has_healthy:
        healthy_elements = [e for e in trace.elements if not e.HasError()]
        assert last_healthy in healthy_elements


@given(
    st.lists(
        st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cf"])),
        min_size=1
    )
)
def test_get_command_with_empty_strings(args):
    """GetCommand includes empty strings which may not be intended."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Add a called component with the given args
    trace.AddCalledComponent(
        component=object(),
        target="func",
        args=args,
        filename=None,
        lineno=None,
        capacity=False
    )
    
    command = trace.GetCommand(include_separators=False)
    
    # Parse the command back using shlex
    parsed_args = shlex.split(command)
    
    # Property: The parsed command should start with the name
    assert parsed_args[0] == "test"
    
    # Check if empty strings are being included (potential bug)
    if '' in args:
        # Empty strings ARE being included in the command
        # This is likely unintended as empty strings as CLI args are unusual
        assert '' in parsed_args[1:]


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1),  # target
            st.lists(st.text()),  # args
        ),
        min_size=1,
        max_size=10
    )
)
def test_trace_element_ordering_fixed(elements_data):
    """Elements added to trace should maintain their order."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    added_elements = []
    for target, args in elements_data:
        trace.AddCalledComponent(
            component=object(),
            target=target,
            args=args,
            filename=None,
            lineno=None,
            capacity=False
        )
        added_elements.append((target, args))
    
    # Property: Elements in trace should be in the same order as added
    # (skipping the initial element at index 0)
    for i, element in enumerate(trace.elements[1:]):
        expected_target, expected_args = added_elements[i]
        # Use underscore-prefixed attribute
        assert element._target == expected_target
        assert element.args == expected_args


@given(
    st.booleans(),  # capacity of last element
    st.booleans(),  # has_separator on last element
    st.booleans(),  # has_error on last element
)
def test_needs_separator_logic(capacity, has_separator, has_error):
    """NeedsSeparator should be consistent with capacity and separator state."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    if has_error:
        # Add a healthy element first, then an error element
        trace.AddCalledComponent(
            component=object(),
            target="func1",
            args=["arg1"],
            filename=None,
            lineno=None,
            capacity=capacity
        )
        element = fire.trace.FireTraceElement(
            component=None,
            action="error",
            target="func2",
            error=Exception("test")
        )
        trace.elements.append(element)
    else:
        # Add a healthy element
        element = fire.trace.FireTraceElement(
            component=object(),
            action="called",
            target="func",
            args=["arg"],
            capacity=capacity
        )
        element._separator = has_separator
        trace.elements.append(element)
    
    needs_sep = trace.NeedsSeparator()
    last_healthy = trace.GetLastHealthyElement()
    
    # Property: NeedsSeparator returns True iff last healthy element has capacity but no separator
    expected = last_healthy.HasCapacity() and not last_healthy.HasSeparator()
    assert needs_sep == expected


@given(
    st.text(min_size=3).map(lambda s: f"--{s}").filter(lambda s: '=' in s)
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_quote_flag_with_equals_fixed(flag_arg):
    """_Quote should properly handle --flag=value arguments."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    quoted = trace._Quote(flag_arg)
    
    # Property: quoted result should be parseable by shlex
    try:
        parsed = shlex.split(quoted)
        # Should parse to exactly one item
        assert len(parsed) == 1
        
        # When parsed and reconstructed, should handle the = correctly
        if '=' in flag_arg:
            prefix, value = flag_arg.split('=', 1)
            # The quote method should quote prefix and value separately
            expected = shlex.quote(prefix) + '=' + shlex.quote(value)
            assert quoted == expected
    except ValueError:
        # If shlex can't parse it, that's a bug
        assert False, f"shlex couldn't parse quoted result: {quoted}"


@given(
    st.lists(st.text(min_size=1), min_size=0, max_size=5),  # args for first call
    st.lists(st.text(min_size=1), min_size=0, max_size=5),  # args for second call
    st.booleans(),  # capacity for first
    st.booleans(),  # capacity for second
)
def test_multiple_add_called_component_fixed(args1, args2, capacity1, capacity2):
    """Multiple AddCalledComponent calls should accumulate correctly."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    # Add first component
    trace.AddCalledComponent(
        component=object(),
        target="func1",
        args=args1,
        filename="file1.py",
        lineno=10,
        capacity=capacity1
    )
    
    # Add second component
    trace.AddCalledComponent(
        component=object(),
        target="func2",
        args=args2,
        filename="file2.py",
        lineno=20,
        capacity=capacity2
    )
    
    # Property: Should have initial element + 2 added elements
    assert len(trace.elements) == 3
    
    # Property: Elements should be in order (using underscore-prefixed attrs)
    assert trace.elements[1]._target == "func1"
    assert trace.elements[1].args == args1
    assert trace.elements[1]._filename == "file1.py"
    assert trace.elements[1]._lineno == 10
    assert trace.elements[1].HasCapacity() == capacity1
    
    assert trace.elements[2]._target == "func2"
    assert trace.elements[2].args == args2
    assert trace.elements[2]._filename == "file2.py"
    assert trace.elements[2]._lineno == 20
    assert trace.elements[2].HasCapacity() == capacity2


@given(
    st.text(min_size=1).filter(lambda s: '\n' not in s and '\r' not in s)
)
def test_quote_special_chars(text):
    """_Quote should properly escape special shell characters."""
    trace = fire.trace.FireTrace(initial_component=object(), name="test")
    
    quoted = trace._Quote(text)
    
    # Property: After quoting, shlex should be able to parse it back to original
    try:
        parsed = shlex.split(quoted)
        assert len(parsed) == 1
        
        # Special handling for --flag=value format
        if text.startswith('--') and '=' in text:
            # Should still parse correctly
            prefix, value = text.split('=', 1)
            expected = shlex.quote(prefix) + '=' + shlex.quote(value)
            assert quoted == expected
            # When parsed, should reconstruct to original
            assert parsed[0] == text
        else:
            # Regular case: quoted text should parse back to original
            assert parsed[0] == text
    except ValueError as e:
        # Quoting failed to produce parseable result
        assert False, f"Failed to parse quoted '{quoted}' from original '{text}': {e}"