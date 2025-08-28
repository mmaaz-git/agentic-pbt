# Bug Report: pyramid.security PermitsResult.msg crashes on malformed format strings

**Target**: `pyramid.security.PermitsResult`, `pyramid.security.Denied`, `pyramid.security.Allowed`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `msg` property of `PermitsResult` and its subclasses (`Denied`, `Allowed`) crashes when the format string contains invalid format specifiers or has mismatched arguments, instead of handling the error gracefully.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.security import Denied

@given(
    fmt_string=st.from_regex(r'[A-Za-z %s]+', fullmatch=True),
    args=st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=3)
)
def test_permits_result_msg_formatting(fmt_string, args):
    """PermitsResult.msg should format string with args"""
    fmt_count = fmt_string.count('%s')
    
    if fmt_count > len(args):
        args = args + [''] * (fmt_count - len(args))
    elif fmt_count < len(args):
        args = args[:fmt_count]
    
    denied = Denied(fmt_string, *args)
    msg = denied.msg  # This can crash
    assert isinstance(msg, str)
```

**Failing input**: `Denied('%A')` or `Denied('%')` or `Denied('%s %s', 'arg1')`

## Reproducing the Bug

```python
from pyramid.security import Denied, Allowed

# Case 1: Invalid format specifier
denied = Denied('%A')
msg = denied.msg  # TypeError: not enough arguments for format string

# Case 2: Incomplete format string  
denied = Denied('%')
msg = denied.msg  # ValueError: incomplete format

# Case 3: Too many format specifiers
allowed = Allowed('%s %s', 'arg1')
msg = allowed.msg  # TypeError: not enough arguments for format string

# Case 4: Wrong type specifier
denied = Denied('%d', 'not_a_number')
msg = denied.msg  # TypeError: %d format: a real number is required, not str
```

## Why This Is A Bug

The `Denied` and `Allowed` classes are public API (exported by pyramid.security) and their docstrings indicate they are returned by security-related APIs. Users may reasonably instantiate these classes directly or modify instances returned by the framework. The `msg` property should handle formatting errors gracefully rather than crashing, especially since format strings might come from user configuration or be constructed dynamically.

## Fix

```diff
--- a/pyramid/security.py
+++ b/pyramid/security.py
@@ -172,7 +172,13 @@ class PermitsResult(int):
     @property
     def msg(self):
         """A string indicating why the result was generated."""
-        return self.s % self.args
+        try:
+            return self.s % self.args
+        except (TypeError, ValueError) as e:
+            # Return a safe representation if formatting fails
+            return 'PermitsResult(fmt=%r, args=%r) [formatting error: %s]' % (
+                self.s, self.args, e
+            )
 
     def __str__(self):
         return self.msg
```