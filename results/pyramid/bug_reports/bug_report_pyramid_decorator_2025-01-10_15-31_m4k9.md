# Bug Report: pyramid_decorator view_config Function Mutation

**Target**: `pyramid_decorator.view_config`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-10

## Summary

The `view_config` decorator mutates the original function by adding a `__view_settings__` attribute directly to it, violating the principle that decorators should not modify original functions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid_decorator

@given(
    settings_list=st.lists(
        st.dictionaries(st.text(min_size=1), st.integers()),
        min_size=1,
        max_size=3
    )
)
def test_view_config_mutation(settings_list):
    def original_func():
        return "test"
    
    # Store initial state
    had_settings_before = hasattr(original_func, '__view_settings__')
    
    # Apply decorators
    decorated = original_func
    for settings in settings_list:
        decorated = pyramid_decorator.view_config(**settings)(decorated)
    
    # Bug: original function is mutated
    assert hasattr(original_func, '__view_settings__')  # Should not be true!
    assert original_func.__view_settings__ == settings_list  # Original mutated!
```

**Failing input**: Any application of the view_config decorator

## Reproducing the Bug

```python
import pyramid_decorator

def my_function():
    return "hello"

def another_function():
    return "world"

# Before decoration
print(hasattr(my_function, '__view_settings__'))  # False

# Decorate first function
decorated1 = pyramid_decorator.view_config(route='route1')(my_function)

# Original function is mutated!
print(hasattr(my_function, '__view_settings__'))  # True - BUG!
print(my_function.__view_settings__)  # [{'route': 'route1'}]

# Decorate it again with different settings
decorated2 = pyramid_decorator.view_config(route='route2')(my_function)

# Settings accumulate on the ORIGINAL function
print(my_function.__view_settings__)  # [{'route': 'route1'}, {'route': 'route2'}]

# This affects all wrapped versions!
```

## Why This Is A Bug

The decorator modifies the original function object by adding `__view_settings__` to it (lines 86-88). This is problematic because:

1. **Violates decorator principles**: Decorators should create new wrapped functions, not modify originals
2. **State leakage**: If the same function is decorated multiple times, the mutations accumulate on the original
3. **Unexpected side effects**: The original function's behavior changes even when used without the decorator
4. **Shared mutable state**: Multiple decorations share the same list, causing interference

## Fix

```diff
def view_config(**settings) -> Callable[[F], F]:
    def decorator(func: F) -> F:
-       # Store configuration on the function
-       if not hasattr(func, '__view_settings__'):
-           func.__view_settings__ = []
-       func.__view_settings__.append(settings)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Simulate view processing
            result = func(*args, **kwargs)
            
            # Apply renderer if specified
            renderer = settings.get('renderer')
            if renderer == 'json':
                import json
                if not isinstance(result, str):
                    result = json.dumps(result)
            elif renderer == 'string':
                result = str(result)
                
            return result
            
-       wrapper.__view_settings__ = func.__view_settings__
+       # Store settings on wrapper, not original
+       # Copy any existing settings from func if it's already decorated
+       existing_settings = getattr(func, '__view_settings__', [])
+       wrapper.__view_settings__ = existing_settings.copy()
+       wrapper.__view_settings__.append(settings)
        return wrapper
        
    return decorator
```