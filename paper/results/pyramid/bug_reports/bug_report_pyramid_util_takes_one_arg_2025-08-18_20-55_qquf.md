# Bug Report: pyramid.util.takes_one_arg Ignores argname Parameter

**Target**: `pyramid.util.takes_one_arg`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `takes_one_arg` function incorrectly returns `True` for any single-argument function when `argname` is specified, regardless of whether the argument name matches the specified `argname`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid.util
import pyramid.viewderivers

@given(st.text(min_size=1).filter(lambda x: x.isidentifier() and x != 'request'))
def test_requestonly_checks_argument_name(arg_name):
    """requestonly should only return True for functions with 'request' argument."""
    func_code = f"def test_func({arg_name}): pass"
    exec(func_code, globals())
    func = globals()['test_func']
    
    result = pyramid.viewderivers.requestonly(func)
    assert result == False, f"requestonly incorrectly returned True for argument named '{arg_name}'"
```

**Failing input**: Any identifier string that is not 'request' (e.g., 'foo', 'xyz', 'req')

## Reproducing the Bug

```python
import pyramid.util
import pyramid.viewderivers

def foo_func(foo):
    pass

result = pyramid.util.takes_one_arg(foo_func, argname='request')
print(f"takes_one_arg(foo_func, argname='request'): {result}")

result2 = pyramid.viewderivers.requestonly(foo_func)
print(f"requestonly(foo_func): {result2}")
```

## Why This Is A Bug

The `takes_one_arg` function has a logic error where it returns `True` for any single-argument function before checking if the argument name matches the specified `argname`. This causes `requestonly` (which calls `takes_one_arg` with `argname='request'`) to incorrectly identify functions as request-only views when their argument is not named 'request', potentially leading to incorrect view mapping behavior in Pyramid.

## Fix

```diff
--- a/pyramid/util.py
+++ b/pyramid/util.py
@@ -679,9 +679,6 @@ def takes_one_arg(callee, attr=None, argname=None):
     if not args:
         return False
 
-    if len(args) == 1:
-        return True
-
     if argname:
 
         defaults = argspec[3]
@@ -691,6 +688,9 @@ def takes_one_arg(callee, attr=None, argname=None):
         if args[0] == argname:
             if len(args) - len(defaults) == 1:
                 return True
+                
+    elif len(args) == 1:
+        return True
 
     return False
```