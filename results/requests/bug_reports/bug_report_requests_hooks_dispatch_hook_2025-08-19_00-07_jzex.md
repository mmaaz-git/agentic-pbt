# Bug Report: requests.hooks.dispatch_hook AttributeError with Non-Dict Hooks

**Target**: `requests.hooks.dispatch_hook`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `dispatch_hook` function crashes with AttributeError when passed non-dict values for the `hooks` parameter, despite being a public API that could receive arbitrary input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.hooks import dispatch_hook

@given(
    hook_data=st.integers()
)
def test_dispatch_hook_invalid_hooks_type(hook_data):
    """Test dispatch_hook when hooks is not a dict or None"""
    # dispatch_hook expects hooks to be a dict or None
    # But doesn't validate this assumption
    
    # With a string (should handle gracefully)
    result = dispatch_hook("test", "not a dict", hook_data)
    assert result == hook_data  # Should return data unchanged
```

**Failing input**: `hook_data=0, hooks="not a dict"`

## Reproducing the Bug

```python
from requests.hooks import dispatch_hook

# Crashes with AttributeError
result = dispatch_hook("test", "not a dict", "some data")
# AttributeError: 'str' object has no attribute 'get'

# Also fails with other non-dict types
dispatch_hook("test", [1, 2, 3], "data")  # AttributeError: 'list' object has no attribute 'get'
dispatch_hook("test", 42, "data")         # AttributeError: 'int' object has no attribute 'get'
```

## Why This Is A Bug

The `dispatch_hook` function is a public API (non-underscore prefixed) in the requests.hooks module and can be imported directly. Its docstring states it "Dispatches a hook dictionary on a given piece of data" but doesn't specify that passing non-dict types will cause an AttributeError. The function should either validate its inputs and raise a clear TypeError, or handle non-dict inputs gracefully by treating them as empty hooks.

## Fix

```diff
def dispatch_hook(key, hooks, hook_data, **kwargs):
    """Dispatches a hook dictionary on a given piece of data."""
    hooks = hooks or {}
+   # Handle non-dict hooks gracefully
+   if not hasattr(hooks, 'get'):
+       return hook_data
    hooks = hooks.get(key)
    if hooks:
        if hasattr(hooks, "__call__"):
            hooks = [hooks]
        for hook in hooks:
            _hook_data = hook(hook_data, **kwargs)
            if _hook_data is not None:
                hook_data = _hook_data
    return hook_data
```