# Bug Report: pyramid_decorator preserve_signature AttributeError

**Target**: `pyramid_decorator.preserve_signature`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-01-10

## Summary

The `preserve_signature` decorator crashes with AttributeError when applied to functions without type annotations, as they lack the `__annotations__` attribute.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid_decorator

@given(
    param_names=st.lists(
        st.text(alphabet='abcdefgh', min_size=1, max_size=3),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_preserve_signature_no_annotations(param_names):
    # Create function without annotations dynamically
    func_str = f"def func({', '.join(param_names)}): return 42"
    local_dict = {}
    exec(func_str, local_dict)
    func = local_dict['func']
    
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    # This crashes with AttributeError
    preserved = pyramid_decorator.preserve_signature(func)(wrapper)
```

**Failing input**: Any function without type annotations

## Reproducing the Bug

```python
import pyramid_decorator

def function_without_annotations(x, y):
    return x + y

def wrapper(*args, **kwargs):
    return function_without_annotations(*args, **kwargs)

# This line crashes with AttributeError
preserved = pyramid_decorator.preserve_signature(function_without_annotations)(wrapper)
# AttributeError: 'function' object has no attribute '__annotations__'
```

## Why This Is A Bug

Functions without type hints don't have an `__annotations__` attribute. The code on line 182 unconditionally accesses `wrapped.__annotations__`, causing an AttributeError. This makes the decorator unusable with any function that lacks type annotations, which is extremely common in Python code.

## Fix

```diff
def preserve_signature(wrapped: Callable) -> Callable[[F], F]:
    def decorator(wrapper: F) -> F:
        # Copy signature from wrapped to wrapper
        wrapper.__signature__ = inspect.signature(wrapped)
-       wrapper.__annotations__ = wrapped.__annotations__
+       wrapper.__annotations__ = getattr(wrapped, '__annotations__', {})
        
        # Preserve other metadata
        functools.update_wrapper(wrapper, wrapped)
        
        return wrapper
        
    return decorator
```