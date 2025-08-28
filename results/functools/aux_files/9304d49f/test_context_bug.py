"""
Test for potential bug in Flask context management
"""

from flask import Flask
from flask.ctx import AppContext, _cv_app
import contextvars


def test_context_pop_order_bug():
    """Test that popping contexts in wrong order causes issues"""
    
    app1 = Flask('app1')
    app2 = Flask('app2')
    
    ctx1 = app1.app_context()
    ctx2 = app2.app_context()
    
    # Push both contexts
    ctx1.push()
    print(f"After ctx1.push(): current context = {_cv_app.get()}")
    
    ctx2.push()
    print(f"After ctx2.push(): current context = {_cv_app.get()}")
    
    # Try to pop ctx1 first (wrong order)
    print("\nAttempting to pop ctx1 (should fail)...")
    try:
        ctx1.pop()
        print("ERROR: ctx1.pop() succeeded when it should have failed!")
    except AssertionError as e:
        print(f"Good: AssertionError raised as expected: {e}")
    except LookupError as e:
        print(f"Unexpected LookupError: {e}")
        print("This might indicate a bug in context management")
    
    # Now pop in correct order
    print("\nPopping in correct order...")
    ctx2.pop()
    print(f"After ctx2.pop(): current context = {_cv_app.get(None)}")
    
    ctx1.pop()
    print(f"After ctx1.pop(): current context = {_cv_app.get(None)}")


def test_multiple_context_tokens():
    """Test how context tokens are managed"""
    
    app = Flask('test_app')
    ctx = app.app_context()
    
    print("Initial state:")
    print(f"  ctx._cv_tokens length: {len(ctx._cv_tokens)}")
    
    # Push the same context multiple times
    for i in range(3):
        ctx.push()
        print(f"After push #{i+1}:")
        print(f"  ctx._cv_tokens length: {len(ctx._cv_tokens)}")
        print(f"  Current context: {_cv_app.get()}")
    
    # Pop the same number of times
    for i in range(3):
        print(f"\nBefore pop #{i+1}:")
        print(f"  ctx._cv_tokens length: {len(ctx._cv_tokens)}")
        ctx.pop()
        print(f"After pop #{i+1}:")
        print(f"  ctx._cv_tokens length: {len(ctx._cv_tokens)}")
        print(f"  Current context: {_cv_app.get(None)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing context pop order bug:")
    print("=" * 60)
    test_context_pop_order_bug()
    
    print("\n" + "=" * 60)
    print("Testing multiple context tokens:")
    print("=" * 60)
    test_multiple_context_tokens()