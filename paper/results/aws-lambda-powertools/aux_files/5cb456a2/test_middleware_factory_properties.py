"""Property-based tests for aws_lambda_powertools.middleware_factory"""

import os
import sys
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the environment path to system path
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator
from aws_lambda_powertools.middleware_factory.exceptions import MiddlewareInvalidArgumentError
from aws_lambda_powertools.shared.functions import strtobool, resolve_truthy_env_var_choice


# Property 1: strtobool should correctly parse all documented truth values
@given(st.sampled_from(['1', 'y', 'yes', 't', 'true', 'on', 'Y', 'YES', 'T', 'TRUE', 'ON']))
def test_strtobool_true_values(value):
    """Test that all documented true values return True"""
    assert strtobool(value) is True


@given(st.sampled_from(['0', 'n', 'no', 'f', 'false', 'off', 'N', 'NO', 'F', 'FALSE', 'OFF']))
def test_strtobool_false_values(value):
    """Test that all documented false values return False"""
    assert strtobool(value) is False


@given(st.text(min_size=1).filter(lambda x: x.lower() not in ['1', 'y', 'yes', 't', 'true', 'on', '0', 'n', 'no', 'f', 'false', 'off']))
def test_strtobool_invalid_values_raise_error(value):
    """Test that invalid values raise ValueError"""
    with pytest.raises(ValueError, match=f"invalid truth value"):
        strtobool(value)


# Property 2: resolve_truthy_env_var_choice should always prefer explicit choice
@given(
    env_str=st.sampled_from(['true', 'false', '1', '0', 'yes', 'no']),
    choice=st.one_of(st.none(), st.booleans())
)
def test_resolve_truthy_env_var_choice_preference(env_str, choice):
    """Test that explicit choice is always preferred over env var"""
    result = resolve_truthy_env_var_choice(env_str, choice)
    if choice is not None:
        assert result == choice
    else:
        assert result == strtobool(env_str)


# Property 3: lambda_handler_decorator should raise error for non-keyword arguments
@given(
    non_keyword_arg=st.one_of(
        st.integers(),
        st.floats(),
        st.text(),
        st.lists(st.integers()),
        st.booleans()
    )
)
def test_lambda_handler_decorator_non_keyword_raises_error(non_keyword_arg):
    """Test that non-keyword arguments raise MiddlewareInvalidArgumentError"""
    
    @lambda_handler_decorator
    def test_middleware(handler, event, context):
        return handler(event, context)
    
    # Trying to use the decorator with a non-keyword argument should raise error
    with pytest.raises(MiddlewareInvalidArgumentError):
        test_middleware(non_keyword_arg)


# Property 4: Decorated middleware should preserve handler execution
@given(
    event_data=st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers(), st.floats())),
    context_data=st.dictionaries(st.text(min_size=1), st.text()),
    return_value=st.one_of(st.text(), st.integers(), st.dictionaries(st.text(), st.text()))
)
def test_middleware_preserves_handler_execution(event_data, context_data, return_value):
    """Test that middleware correctly passes through to handler and returns its result"""
    
    @lambda_handler_decorator
    def passthrough_middleware(handler, event, context):
        # This middleware does nothing, just passes through
        return handler(event, context)
    
    @passthrough_middleware
    def test_handler(event, context):
        # Verify we received the correct event and context
        assert event == event_data
        assert context == context_data
        return return_value
    
    result = test_handler(event_data, context_data)
    assert result == return_value


# Property 5: Middleware with kwargs should work correctly
@given(
    event_data=st.dictionaries(st.text(min_size=1), st.text()),
    context_data=st.dictionaries(st.text(min_size=1), st.text()),
    kwarg_value=st.text()
)
def test_middleware_with_kwargs(event_data, context_data, kwarg_value):
    """Test that middleware with keyword arguments works correctly"""
    
    @lambda_handler_decorator
    def middleware_with_kwargs(handler, event, context, test_kwarg=None):
        # Verify the kwarg was passed
        assert test_kwarg == kwarg_value
        return handler(event, context)
    
    @middleware_with_kwargs(test_kwarg=kwarg_value)
    def test_handler(event, context):
        return {"success": True}
    
    result = test_handler(event_data, context_data)
    assert result == {"success": True}


# Property 6: Multiple middlewares should compose correctly
@given(
    event_data=st.dictionaries(st.text(min_size=1), st.text()),
    context_data=st.dictionaries(st.text(min_size=1), st.text())
)
def test_multiple_middlewares_compose(event_data, context_data):
    """Test that multiple middlewares can be stacked and execute in correct order"""
    execution_order = []
    
    @lambda_handler_decorator
    def middleware1(handler, event, context):
        execution_order.append("middleware1_before")
        result = handler(event, context)
        execution_order.append("middleware1_after")
        return result
    
    @lambda_handler_decorator
    def middleware2(handler, event, context):
        execution_order.append("middleware2_before")
        result = handler(event, context)
        execution_order.append("middleware2_after")
        return result
    
    @middleware1
    @middleware2
    def test_handler(event, context):
        execution_order.append("handler")
        return "done"
    
    result = test_handler(event_data, context_data)
    
    # Verify execution order
    assert execution_order == [
        "middleware1_before",
        "middleware2_before", 
        "handler",
        "middleware2_after",
        "middleware1_after"
    ]
    assert result == "done"


# Property 7: Exception propagation
@given(
    event_data=st.dictionaries(st.text(min_size=1), st.text()),
    context_data=st.dictionaries(st.text(min_size=1), st.text()),
    error_message=st.text(min_size=1)
)
def test_exception_propagation(event_data, context_data, error_message):
    """Test that exceptions in handler are properly propagated through middleware"""
    
    @lambda_handler_decorator
    def test_middleware(handler, event, context):
        return handler(event, context)
    
    @test_middleware
    def failing_handler(event, context):
        raise ValueError(error_message)
    
    with pytest.raises(ValueError, match=error_message):
        failing_handler(event_data, context_data)


# Property 8: Trace execution flag handling
@given(
    trace_flag=st.one_of(st.none(), st.booleans()),
    event_data=st.dictionaries(st.text(min_size=1), st.text()),
    context_data=st.dictionaries(st.text(min_size=1), st.text())
)
def test_trace_execution_flag(trace_flag, event_data, context_data):
    """Test that trace_execution parameter is handled correctly"""
    
    # Set env var to false to have a baseline
    os.environ['POWERTOOLS_TRACE_MIDDLEWARES'] = 'false'
    
    @lambda_handler_decorator(trace_execution=trace_flag)
    def test_middleware(handler, event, context):
        return handler(event, context)
    
    @test_middleware
    def test_handler(event, context):
        return "success"
    
    # Should not raise any errors regardless of trace_flag value
    result = test_handler(event_data, context_data)
    assert result == "success"


if __name__ == "__main__":
    # Run with increased examples for thoroughness
    settings.register_profile("thorough", max_examples=1000)
    settings.load_profile("thorough")
    pytest.main([__file__, "-v"])