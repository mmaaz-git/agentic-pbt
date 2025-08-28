"""Minimal reproduction of the bug in pyramid.tweens._error_handler"""

import sys
from unittest.mock import Mock
from pyramid.tweens import _error_handler
from pyramid.httpexceptions import HTTPNotFound


def reproduce_bug():
    """Reproduce the bug where _error_handler fails when called outside exception context."""
    # Create a mock request that raises HTTPNotFound
    request = Mock()
    request.invoke_exception_view = Mock(side_effect=HTTPNotFound())
    
    # Create an exception (but we're not in an exception context)
    original_exc = ValueError("Test error")
    
    # This should re-raise the original exception, but instead crashes
    try:
        _error_handler(request, original_exc)
    except TypeError as e:
        print(f"BUG FOUND: {e}")
        print(f"Error type: {type(e).__name__}")
        return True
    except ValueError:
        print("Original exception was re-raised correctly")
        return False
    
    return False


if __name__ == "__main__":
    print("Testing pyramid.tweens._error_handler...")
    print()
    
    # Show the issue
    print("When _error_handler is called with an exception but not from an exception context:")
    print("(i.e., sys.exc_info() returns (None, None, None))")
    print()
    
    if reproduce_bug():
        print("\nThe bug occurs because:")
        print("1. _error_handler calls sys.exc_info() which returns (None, None, None)")
        print("2. It passes this to reraise(None, None, None)")
        print("3. reraise tries to execute: value = tp() where tp is None")
        print("4. This causes TypeError: 'NoneType' object is not callable")