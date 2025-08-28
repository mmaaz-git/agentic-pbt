"""Detailed test showing the bug in pyramid.tweens._error_handler"""

import sys
import traceback
from unittest.mock import Mock
from pyramid.tweens import _error_handler, excview_tween_factory
from pyramid.httpexceptions import HTTPNotFound


def test_error_handler_in_exception_context():
    """Test that _error_handler works correctly when called from exception context."""
    print("Test 1: _error_handler called from within exception context")
    
    request = Mock()
    request.invoke_exception_view = Mock(side_effect=HTTPNotFound())
    
    try:
        raise ValueError("Original error")
    except ValueError as exc:
        # We're in an exception context, sys.exc_info() will return valid data
        try:
            _error_handler(request, exc)
            print("  ERROR: Should have re-raised!")
        except ValueError as re_raised:
            print(f"  ✓ Correctly re-raised: {re_raised}")
        except TypeError as type_err:
            print(f"  ✗ Got TypeError instead: {type_err}")


def test_error_handler_outside_exception_context():
    """Test that _error_handler fails when called outside exception context."""
    print("\nTest 2: _error_handler called outside exception context")
    
    request = Mock()
    request.invoke_exception_view = Mock(side_effect=HTTPNotFound())
    
    # Create exception but we're NOT in an exception context
    exc = ValueError("Test error")
    
    try:
        _error_handler(request, exc)
        print("  ERROR: Should have raised something!")
    except ValueError as re_raised:
        print(f"  ✓ Correctly re-raised: {re_raised}")
    except TypeError as type_err:
        print(f"  ✗ BUG - Got TypeError: {type_err}")


def test_normal_tween_usage():
    """Test that the bug doesn't affect normal tween usage."""
    print("\nTest 3: Normal tween usage (excview_tween_factory)")
    
    # Create a handler that raises an exception
    handler = Mock(side_effect=ValueError("Handler error"))
    registry = Mock()
    
    # Create request with invoke_exception_view that raises HTTPNotFound
    request = Mock()
    request.invoke_exception_view = Mock(side_effect=HTTPNotFound())
    
    # Create and use the tween
    tween = excview_tween_factory(handler, registry)
    
    try:
        tween(request)
        print("  ERROR: Should have raised ValueError!")
    except ValueError as exc:
        print(f"  ✓ Works correctly in normal usage: {exc}")
    except TypeError as type_err:
        print(f"  ✗ TypeError even in normal usage: {type_err}")


def analyze_issue():
    """Analyze the root cause of the issue."""
    print("\nAnalysis of the issue:")
    print("-" * 40)
    
    # Show what sys.exc_info() returns in different contexts
    print("sys.exc_info() outside exception context:", sys.exc_info())
    
    try:
        raise ValueError("test")
    except:
        print("sys.exc_info() inside exception context:", sys.exc_info()[:2], "...")
    
    print("\nThe bug occurs because _error_handler assumes it's always")
    print("called from within an exception context (where sys.exc_info()")
    print("returns valid exception info), but it can be called with an")
    print("exception object directly, outside of an exception context.")


if __name__ == "__main__":
    test_error_handler_in_exception_context()
    test_error_handler_outside_exception_context()
    test_normal_tween_usage()
    analyze_issue()