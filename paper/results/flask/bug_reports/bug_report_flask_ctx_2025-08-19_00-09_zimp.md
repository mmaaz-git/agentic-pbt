# Bug Report: flask.ctx Context Stack Corruption After Wrong Pop Order

**Target**: `flask.ctx.AppContext.pop` and `flask.ctx.RequestContext.pop`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Flask's context management system becomes corrupted when attempting to pop contexts out of order, preventing proper cleanup of remaining contexts on the stack.

## Property-Based Test

```python
from hypothesis import given
import hypothesis.strategies as st
import flask
import flask.ctx

@given(st.just(flask.Flask('test')))
def test_wrong_context_pop_raises_error(app):
    """Test that popping the wrong context raises AssertionError."""
    ctx1 = flask.ctx.AppContext(app)
    ctx2 = flask.ctx.AppContext(app)
    
    ctx1.push()
    ctx2.push()
    
    # Try to pop ctx1 when ctx2 is on top - should raise
    try:
        ctx1.pop()
        assert False, "Should have raised AssertionError"
    except AssertionError as e:
        assert "Popped wrong" in str(e)
        # Clean up - this fails with LookupError
        ctx2.pop()
        ctx1.pop()
```

**Failing input**: Any Flask app instance

## Reproducing the Bug

```python
import flask
import flask.ctx

app = flask.Flask('test')

ctx1 = flask.ctx.AppContext(app)
ctx2 = flask.ctx.AppContext(app)

ctx1.push()
ctx2.push()

try:
    ctx1.pop()
except AssertionError:
    pass

try:
    ctx2.pop()
except LookupError as e:
    print(f"Context stack corrupted: {e}")
```

## Why This Is A Bug

When contexts are popped out of order, Flask correctly detects the error and raises an AssertionError. However, the pop() method has already modified the internal state (removed the token and reset the context variable) before checking if the pop order is correct. This leaves the context stack in a corrupted state where:

1. The context variable has been reset but contexts remain on the logical stack
2. Subsequent attempts to pop the remaining contexts fail with LookupError
3. There's no way to recover or clean up the stack properly

This violates the principle that error detection should not corrupt the state, especially for recoverable errors.

## Fix

```diff
--- a/flask/ctx.py
+++ b/flask/ctx.py
@@ -255,15 +255,16 @@ class AppContext:
 
     def pop(self, exc: BaseException | None = _sentinel) -> None:  # type: ignore
         """Pops the app context."""
+        ctx = _cv_app.get()
+        if ctx is not self:
+            raise AssertionError(
+                f"Popped wrong app context. ({ctx!r} instead of {self!r})"
+            )
+            
         try:
             if len(self._cv_tokens) == 1:
                 if exc is _sentinel:
                     exc = sys.exc_info()[1]
                 self.app.do_teardown_appcontext(exc)
         finally:
-            ctx = _cv_app.get()
             _cv_app.reset(self._cv_tokens.pop())
 
-        if ctx is not self:
-            raise AssertionError(
-                f"Popped wrong app context. ({ctx!r} instead of {self!r})"
-            )
 
         appcontext_popped.send(self.app, _async_wrapper=self.app.ensure_sync)
```

The same fix should be applied to RequestContext.pop() which has the identical issue:

```diff
--- a/flask/ctx.py
+++ b/flask/ctx.py
@@ -455,6 +455,11 @@ class RequestContext:
         .. versionchanged:: 0.9
            Added the `exc` argument.
         """
+        ctx = _cv_request.get()
+        if ctx is not self:
+            raise AssertionError(
+                f"Popped wrong request context. ({ctx!r} instead of {self!r})"
+            )
+        
         clear_request = len(self._cv_tokens) == 1
 
         try:
@@ -478,11 +483,6 @@ class RequestContext:
             token, app_ctx = self._cv_tokens.pop()
             _cv_request.reset(token)
 
-            # get rid of circular dependencies at the end of the request
-            # so that we don't require the GC to be active.
-            ctx = _cv_request.get()
-            if ctx is not self:
-                raise AssertionError(
-                    f"Popped wrong request context. ({ctx!r} instead of {self!r})"
-                )
+            # get rid of circular dependencies at the end of the request
             self.session = _no_session
```