"""
Test that demonstrates context corruption bug in Flask
"""

from flask import Flask
from flask.ctx import _cv_app
import contextvars


def test_context_corruption_after_wrong_pop():
    """
    When popping contexts in wrong order, Flask raises AssertionError
    but the context state becomes corrupted.
    """
    
    app1 = Flask('app1')
    app2 = Flask('app2')
    
    ctx1 = app1.app_context()
    ctx2 = app2.app_context()
    
    # Push both contexts
    ctx1.push()
    ctx2.push()
    
    print("Initial state:")
    print(f"  ctx1._cv_tokens: {len(ctx1._cv_tokens)} tokens")
    print(f"  ctx2._cv_tokens: {len(ctx2._cv_tokens)} tokens")
    print(f"  Current context: {_cv_app.get()}")
    
    # Try to pop ctx1 (wrong order) - this will fail but corrupt state
    print("\nAttempting wrong pop (ctx1)...")
    try:
        ctx1.pop()
    except AssertionError as e:
        print(f"  AssertionError caught: {e}")
    
    # Check state after failed pop
    print("\nState after failed pop:")
    print(f"  ctx1._cv_tokens: {len(ctx1._cv_tokens)} tokens")  
    print(f"  ctx2._cv_tokens: {len(ctx2._cv_tokens)} tokens")
    try:
        current = _cv_app.get()
        print(f"  Current context: {current}")
    except LookupError:
        print(f"  Current context: LookupError - context var is empty!")
    
    # Now try to pop ctx2 (should be correct order but will fail)
    print("\nAttempting to pop ctx2 (should work but won't)...")
    try:
        ctx2.pop()
        print("  SUCCESS: ctx2 popped")
    except LookupError as e:
        print(f"  FAILURE: LookupError - {e}")
        print("  This is a BUG: The context variable was incorrectly cleared")
    
    # Try to access context
    print("\nFinal state:")
    try:
        current = _cv_app.get()
        print(f"  Current context: {current}")
    except LookupError:
        print(f"  Current context: LookupError - no context available")
    
    print(f"  ctx1._cv_tokens: {len(ctx1._cv_tokens)} tokens")
    print(f"  ctx2._cv_tokens: {len(ctx2._cv_tokens)} tokens")


if __name__ == "__main__":
    test_context_corruption_after_wrong_pop()