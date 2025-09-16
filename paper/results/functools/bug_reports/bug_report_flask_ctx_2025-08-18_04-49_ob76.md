# Bug Report: flask.ctx AppContext Context Variable Corruption on Wrong Pop Order

**Target**: `flask.ctx.AppContext.pop`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When AppContext.pop() is called on the wrong context (not the most recently pushed), Flask correctly raises an AssertionError but incorrectly clears the context variable, leaving the application in a corrupted state.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from flask import Flask
from flask.ctx import _cv_app

def test_app_context_pop_wrong_context_assertion():
    """Property: Popping wrong app context raises AssertionError without corrupting state"""
    app1 = Flask('app1')
    app2 = Flask('app2')
    
    ctx1 = app1.app_context()
    ctx2 = app2.app_context()
    
    ctx1.push()
    ctx2.push()
    
    # Try to pop ctx1 when ctx2 is on top - should fail
    with pytest.raises(AssertionError, match="Popped wrong app context"):
        ctx1.pop()
    
    # State should not be corrupted - ctx2 should still be poppable
    ctx2.pop()  # This fails with LookupError due to the bug
    ctx1.pop()
```

**Failing input**: Attempting to pop contexts in wrong order

## Reproducing the Bug

```python
from flask import Flask
from flask.ctx import _cv_app

app1 = Flask('app1')
app2 = Flask('app2')

ctx1 = app1.app_context()
ctx2 = app2.app_context()

ctx1.push()
ctx2.push()

try:
    ctx1.pop()
except AssertionError:
    pass

try:
    current = _cv_app.get()
except LookupError:
    print("BUG: Context variable is empty after failed pop")

try:
    ctx2.pop()
except LookupError as e:
    print(f"BUG: Cannot pop ctx2: {e}")
```

## Why This Is A Bug

The AppContext.pop() method modifies the context variable state (by calling `_cv_app.reset()`) before verifying that the correct context is being popped. When popping in the wrong order:

1. The method removes the token from `self._cv_tokens` 
2. Calls `_cv_app.reset()` which clears the context variable
3. Only then checks if the context being popped is correct
4. Raises AssertionError if wrong, but damage is already done

This leaves the application in an inconsistent state where the context variable is empty but contexts still have tokens that should be valid.

## Fix

```diff
--- a/flask/ctx.py
+++ b/flask/ctx.py
@@ -256,13 +256,15 @@ class AppContext:
     def pop(self, exc: BaseException | None = _sentinel) -> None:  # type: ignore
         """Pops the app context."""
         try:
             if len(self._cv_tokens) == 1:
                 if exc is _sentinel:
                     exc = sys.exc_info()[1]
                 self.app.do_teardown_appcontext(exc)
         finally:
             ctx = _cv_app.get()
+            if ctx is not self:
+                raise AssertionError(
+                    f"Popped wrong app context. ({ctx!r} instead of {self!r})"
+                )
             _cv_app.reset(self._cv_tokens.pop())
 
-        if ctx is not self:
-            raise AssertionError(
-                f"Popped wrong app context. ({ctx!r} instead of {self!r})"
-            )
 
         appcontext_popped.send(self.app, _async_wrapper=self.app.ensure_sync)
```