"""Property-based tests for pyramid.tweens module."""

import sys
import traceback
from unittest.mock import Mock, MagicMock

from hypothesis import given, strategies as st, assume, settings
import pytest

from pyramid.tweens import (
    _error_handler,
    excview_tween_factory,
    MAIN,
    INGRESS,
    EXCVIEW,
)
from pyramid.httpexceptions import HTTPNotFound
from pyramid.util import reraise


# Test 1: Constants are immutable strings
def test_constants_are_strings():
    """Test that module constants are strings and have expected values."""
    assert isinstance(MAIN, str)
    assert isinstance(INGRESS, str)
    assert isinstance(EXCVIEW, str)
    assert MAIN == 'MAIN'
    assert INGRESS == 'INGRESS'
    assert EXCVIEW == 'pyramid.tweens.excview_tween_factory'


# Test 2: excview_tween_factory returns a callable tween
@given(st.data())
def test_excview_tween_factory_returns_callable(data):
    """Test that excview_tween_factory always returns a callable tween."""
    # Create mock handler and registry
    handler = Mock(return_value="response")
    registry = Mock()
    
    # Factory should return a callable tween
    tween = excview_tween_factory(handler, registry)
    assert callable(tween)
    
    # The returned tween should accept a request
    request = Mock()
    response = tween(request)
    assert response == "response"
    handler.assert_called_once_with(request)


# Test 3: Tween catches and handles exceptions
@given(
    st.text(min_size=1, max_size=100),  # exception message
    st.integers(min_value=1, max_value=10),  # exception type seed
)
def test_tween_catches_exceptions(exc_message, exc_type_seed):
    """Test that the tween catches exceptions from the handler."""
    # Choose an exception type based on seed
    exc_types = [ValueError, TypeError, RuntimeError, KeyError, AttributeError]
    exc_type = exc_types[exc_type_seed % len(exc_types)]
    
    # Create a handler that raises an exception
    handler = Mock(side_effect=exc_type(exc_message))
    registry = Mock()
    
    # Create mock request with invoke_exception_view
    request = Mock()
    request.invoke_exception_view = Mock(return_value="error_response")
    
    # Create and call the tween
    tween = excview_tween_factory(handler, registry)
    response = tween(request)
    
    # Should have caught the exception and returned error response
    assert response == "error_response"
    handler.assert_called_once_with(request)
    request.invoke_exception_view.assert_called_once()
    
    # Check that exc_info was passed correctly
    exc_info_arg = request.invoke_exception_view.call_args[0][0]
    assert exc_info_arg[0] == exc_type
    assert str(exc_info_arg[1]) == exc_message


# Test 4: HTTPNotFound causes re-raise of original exception
@given(
    st.text(min_size=1, max_size=100),  # original exception message
)
def test_error_handler_reraises_on_httpnotfound(exc_message):
    """Test that _error_handler re-raises original exception when HTTPNotFound is raised."""
    # Create a mock request that raises HTTPNotFound
    request = Mock()
    request.invoke_exception_view = Mock(side_effect=HTTPNotFound())
    
    # Create original exception
    original_exc = ValueError(exc_message)
    
    # Call _error_handler and expect it to re-raise
    with pytest.raises(ValueError) as exc_info:
        _error_handler(request, original_exc)
    
    assert str(exc_info.value) == exc_message


# Test 5: Test reraise preserves traceback
@given(
    st.text(min_size=1, max_size=100),  # exception message
)
def test_reraise_preserves_traceback(exc_message):
    """Test that reraise preserves the original traceback."""
    # Create an exception with a traceback
    try:
        raise ValueError(exc_message)
    except ValueError:
        original_exc_info = sys.exc_info()
    
    # Use reraise to re-raise the exception
    with pytest.raises(ValueError) as exc_info:
        reraise(*original_exc_info)
    
    # Check that the exception message is preserved
    assert str(exc_info.value) == exc_message
    
    # Check that traceback is preserved (it should contain this function)
    tb_summary = traceback.extract_tb(exc_info.tb)
    function_names = [frame.name for frame in tb_summary]
    assert 'test_reraise_preserves_traceback' in function_names


# Test 6: Multiple nested tweens work correctly
@given(
    st.lists(st.booleans(), min_size=1, max_size=5),  # whether each handler raises
    st.text(min_size=1, max_size=100),  # exception message
)
def test_nested_tweens(handler_raises_flags, exc_message):
    """Test that multiple nested tweens handle exceptions correctly."""
    registry = Mock()
    
    # Create the innermost handler
    if handler_raises_flags[-1]:
        innermost_handler = Mock(side_effect=ValueError(exc_message))
    else:
        innermost_handler = Mock(return_value="success_response")
    
    # Build chain of tweens
    current_handler = innermost_handler
    for raises in reversed(handler_raises_flags[:-1]):
        if raises:
            # This level will raise
            intermediate_handler = Mock(side_effect=ValueError(exc_message))
            tween = excview_tween_factory(intermediate_handler, registry)
        else:
            # This level will pass through
            tween = excview_tween_factory(current_handler, registry)
        current_handler = tween
    
    # Create request with invoke_exception_view
    request = Mock()
    request.invoke_exception_view = Mock(return_value="error_response")
    
    # Call the outermost tween
    response = current_handler(request)
    
    # If any handler raises, we should get error_response
    if any(handler_raises_flags):
        assert response == "error_response"
    else:
        assert response == "success_response"


# Test 7: Factory is idempotent with respect to functionality
@given(st.data())
def test_factory_idempotent(data):
    """Test that calling the factory multiple times produces functionally equivalent tweens."""
    handler = Mock(return_value="response")
    registry = Mock()
    
    # Create multiple tweens from the same factory
    tween1 = excview_tween_factory(handler, registry)
    tween2 = excview_tween_factory(handler, registry)
    
    # Both should be callable and different objects
    assert callable(tween1)
    assert callable(tween2)
    assert tween1 is not tween2
    
    # But they should behave the same
    request = Mock()
    response1 = tween1(request)
    
    handler.reset_mock()
    response2 = tween2(request)
    
    assert response1 == response2 == "response"


# Test 8: Test edge case with None values
@given(st.data())
def test_none_handling(data):
    """Test handling of None values in various positions."""
    # Handler returns None
    handler = Mock(return_value=None)
    registry = Mock()
    
    tween = excview_tween_factory(handler, registry)
    request = Mock()
    
    response = tween(request)
    assert response is None
    
    # Handler raises exception, invoke_exception_view returns None
    handler2 = Mock(side_effect=ValueError("test"))
    tween2 = excview_tween_factory(handler2, registry)
    
    request2 = Mock()
    request2.invoke_exception_view = Mock(return_value=None)
    
    response2 = tween2(request2)
    assert response2 is None


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])