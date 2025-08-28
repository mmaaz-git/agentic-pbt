# Bug Report: click.globals Type Confusion Vulnerability

**Target**: `click.globals.get_current_context`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

`get_current_context()` returns incorrect values instead of raising `RuntimeError` when the internal `_local.stack` is corrupted to a string type, violating the function's contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from click.globals import get_current_context, _local, pop_context

@given(st.text(min_size=1))
@settings(max_examples=1000)
def test_string_stack_returns_last_char(test_string):
    # Clear any existing context
    while get_current_context(silent=True) is not None:
        try:
            pop_context()
        except:
            break
    
    # Set stack to a string (simulating corruption)
    _local.stack = test_string
    
    # get_current_context should raise RuntimeError for invalid stack
    # But it actually returns the last character for strings
    result = get_current_context(silent=False)
    
    # This demonstrates the bug: it returns the last character
    assert result == test_string[-1]
```

**Failing input**: Any non-empty string, e.g., `"corrupted"`

## Reproducing the Bug

```python
from click.globals import get_current_context, _local

_local.stack = "corrupted"

result = get_current_context(silent=False)
print(f"Returned: '{result}'")  # Output: Returned: 'd'
```

## Why This Is A Bug

The function `get_current_context()` is documented to either return a `Context` object or raise `RuntimeError` when no context is available. When `_local.stack` is corrupted to a string type (which could happen if external code incorrectly manipulates thread-local storage), the function returns the last character of the string instead of raising an appropriate error. This violates the function's contract and could lead to type confusion errors downstream.

The bug occurs because Python allows indexing strings with `[-1]`, so `_local.stack[-1]` succeeds when `stack` is a string, returning the last character instead of raising the expected exception.

## Fix

```diff
--- a/click/globals.py
+++ b/click/globals.py
@@ -33,6 +33,8 @@ def get_current_context(silent: bool = False) -> Context | None:
                    :exc:`RuntimeError`.
     """
     try:
+        if not isinstance(getattr(_local, 'stack', None), list):
+            raise AttributeError("Invalid stack type")
         return t.cast("Context", _local.stack[-1])
     except (AttributeError, IndexError) as e:
         if not silent:
```