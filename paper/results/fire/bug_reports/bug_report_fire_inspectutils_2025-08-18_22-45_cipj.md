# Bug Report: fire.inspectutils GetFullArgSpec Fails with Metaclass __call__

**Target**: `fire.inspectutils.GetFullArgSpec`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

GetFullArgSpec fails to extract __init__ parameters from classes that have a metaclass overriding __call__, returning generic *args/**kwargs instead.

## Property-Based Test

```python
class MetaWithCall(type):
    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)

class TestClass(metaclass=MetaWithCall):
    def __init__(self, x, y=5):
        self.x = x
        self.y = y

# Test property: GetFullArgSpec should extract __init__ parameters
spec = inspectutils.GetFullArgSpec(TestClass)
assert spec.args == ['x', 'y']  # FAILS: spec.args is []
assert spec.defaults == (5,)     # FAILS: spec.defaults is ()
```

**Failing input**: Any class with a metaclass that overrides `__call__`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils

class MetaWithCall(type):
    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)

class BuggyClass(metaclass=MetaWithCall):
    def __init__(self, x, y=5):
        self.x = x
        self.y = y

spec = inspectutils.GetFullArgSpec(BuggyClass)
print(f"args: {spec.args}")      # Output: []
print(f"varargs: {spec.varargs}")  # Output: args
print(f"varkw: {spec.varkw}")      # Output: kwargs

# Expected: args=['x', 'y'], defaults=(5,)
# Actual: args=[], varargs='args', varkw='kwargs'
```

## Why This Is A Bug

When Fire uses GetFullArgSpec to determine how to call a class, it needs the __init__ parameters to properly parse command-line arguments. With this bug, Fire would incorrectly think the class accepts *args/**kwargs instead of the specific parameters x and y, breaking command-line interface generation for classes with such metaclasses.

## Fix

The issue occurs because Python's `inspect._signature_from_callable` returns the metaclass's __call__ signature instead of the class's __init__ signature. A fix would need to detect this case and explicitly use the __init__ method:

```diff
--- a/fire/inspectutils.py
+++ b/fire/inspectutils.py
@@ -101,10 +101,22 @@ def Py3GetFullArgSpec(fn):
   """
   # pylint: disable=no-member
 
+  # Check if fn is a class with a metaclass that overrides __call__
+  if inspect.isclass(fn):
+    metaclass = type(fn)
+    if hasattr(metaclass, '__call__') and metaclass.__call__ is not type.__call__:
+      # Use __init__ directly for classes with custom metaclass __call__
+      if hasattr(fn, '__init__'):
+        fn = fn.__init__
+        skip_bound_arg = True
+      else:
+        fn = lambda self: None  # Default __init__
+        skip_bound_arg = True
+
   try:
     sig = inspect._signature_from_callable(  # pylint: disable=protected-access  # type: ignore
         fn,
-        skip_bound_arg=True,
+        skip_bound_arg=skip_bound_arg if 'skip_bound_arg' in locals() else True,
         follow_wrapper_chains=True,
         sigcls=inspect.Signature)
   except Exception:
```