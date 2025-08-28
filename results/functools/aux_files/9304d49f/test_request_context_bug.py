"""
Test that demonstrates the same context corruption bug in RequestContext
"""

from flask import Flask
from flask.ctx import _cv_request
import sys


def test_request_context_corruption_after_wrong_pop():
    """
    RequestContext has the same bug as AppContext - wrong pop corrupts state
    """
    
    app = Flask('test_app')
    
    environ1 = {
        'REQUEST_METHOD': 'GET',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'PATH_INFO': '/path1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': sys.stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False
    }
    
    environ2 = environ1.copy()
    environ2['PATH_INFO'] = '/path2'
    
    ctx1 = app.request_context(environ1)
    ctx2 = app.request_context(environ2)
    
    # Push both contexts
    ctx1.push()
    ctx2.push()
    
    print("Initial state:")
    print(f"  ctx1._cv_tokens: {len(ctx1._cv_tokens)} tokens")
    print(f"  ctx2._cv_tokens: {len(ctx2._cv_tokens)} tokens")
    print(f"  Current request context: {_cv_request.get()}")
    
    # Try to pop ctx1 (wrong order) - this will fail but corrupt state
    print("\nAttempting wrong pop (ctx1)...")
    try:
        ctx1.pop()
    except AssertionError as e:
        print(f"  AssertionError caught: {e}")
    except Exception as e:
        print(f"  Other error: {type(e).__name__}: {e}")
    
    # Check state after failed pop
    print("\nState after failed pop:")
    print(f"  ctx1._cv_tokens: {len(ctx1._cv_tokens)} tokens")  
    print(f"  ctx2._cv_tokens: {len(ctx2._cv_tokens)} tokens")
    try:
        current = _cv_request.get()
        print(f"  Current request context: {current}")
    except LookupError:
        print(f"  Current request context: LookupError - context var is empty!")
    
    # Now try to pop ctx2 (should be correct order but will fail)
    print("\nAttempting to pop ctx2 (should work but won't)...")
    try:
        ctx2.pop()
        print("  SUCCESS: ctx2 popped")
    except LookupError as e:
        print(f"  FAILURE: LookupError - {e}")
        print("  This is a BUG: The request context variable was incorrectly cleared")
    except RuntimeError as e:
        print(f"  FAILURE: RuntimeError - {e}")
        print("  The state is corrupted")


if __name__ == "__main__":
    test_request_context_corruption_after_wrong_pop()