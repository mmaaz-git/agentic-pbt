# Bug Report: flask.views.View Decorator Application Order Reversal

**Target**: `flask.views.View.as_view`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

View.as_view applies decorators from the `decorators` class attribute in reverse order, causing unexpected behavior when decorator order matters for correctness.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from flask.views import View
import flask

@given(num_decorators=st.integers(min_value=2, max_value=5))
def test_view_decorator_order(num_decorators):
    app = flask.Flask(__name__)
    call_order = []
    test_decorators = []
    
    for i in range(num_decorators):
        def make_decorator(idx):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    call_order.append(idx)
                    return func(*args, **kwargs)
                return wrapper
            return decorator
        test_decorators.append(make_decorator(i))
    
    class TestView(View):
        decorators = test_decorators
        def dispatch_request(self):
            return "response"
    
    with app.app_context():
        view_func = TestView.as_view("test")
        view_func()
        
    assert call_order == list(range(num_decorators))
```

**Failing input**: `num_decorators=2` (or any value >= 2)

## Reproducing the Bug

```python
import flask
from flask.views import View

app = flask.Flask(__name__)
call_order = []

def decorator1(func):
    def wrapper(*args, **kwargs):
        call_order.append(1)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def decorator2(func):
    def wrapper(*args, **kwargs):
        call_order.append(2)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

class TestView(View):
    decorators = [decorator1, decorator2]
    
    def dispatch_request(self):
        return 'response'

with app.app_context():
    view_func = TestView.as_view('test')
    view_func()
    
print(f'Actual order: {call_order}')    # [2, 1]
print(f'Expected order: [1, 2]')         # [1, 2]

assert call_order == [1, 2], f"Decorators applied in wrong order: {call_order}"
```

## Why This Is A Bug

When decorators are specified in a list like `[decorator1, decorator2]`, the natural expectation is that decorator1 will be applied first (outermost), followed by decorator2. This matches how decorators work in standard Python:

```python
@decorator1
@decorator2
def func(): pass
# Equivalent to: func = decorator1(decorator2(func))
# Call order: decorator1 executes first
```

However, Flask's implementation applies them in reverse order, causing decorator2 to execute first. This violates the principle of least surprise and can cause bugs when:
- Authentication/authorization decorators need specific ordering
- Logging/timing decorators need to wrap other decorators
- Transaction management decorators need proper nesting
- Any scenario where decorator execution order affects correctness

## Fix

The issue is in the View.as_view method which iterates through decorators in forward order but needs to apply them in reverse to match expected behavior:

```diff
@classmethod
def as_view(cls, name: str, *class_args: t.Any, **class_kwargs: t.Any) -> ft.RouteCallable:
    # ... previous code ...
    
    if cls.decorators:
        view.__name__ = name
        view.__module__ = cls.__module__
-       for decorator in cls.decorators:
+       for decorator in reversed(cls.decorators):
            view = decorator(view)
    
    # ... rest of method ...
```

Alternatively, document this behavior clearly if it's intentional, though this would be surprising to most Python developers.