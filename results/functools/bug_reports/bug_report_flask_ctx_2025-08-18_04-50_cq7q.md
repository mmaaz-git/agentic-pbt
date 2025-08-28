# Bug Report: flask.ctx Context Variable Corruption on Wrong Pop Order

**Target**: `flask.ctx.AppContext.pop` and `flask.ctx.RequestContext.pop`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Both AppContext and RequestContext in Flask have a critical bug where calling pop() on the wrong context (not the most recently pushed) correctly raises an AssertionError but incorrectly clears the context variable, leaving the application in a corrupted state where subsequent operations fail.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from flask import Flask
from flask.ctx import _cv_app, _cv_request
import sys

def test_context_pop_wrong_order_preserves_state():
    """Property: Popping contexts in wrong order should raise error without corrupting state"""
    
    # Test AppContext
    app1 = Flask('app1')
    app2 = Flask('app2')
    
    ctx1 = app1.app_context()
    ctx2 = app2.app_context()
    
    ctx1.push()
    ctx2.push()
    
    # Try to pop ctx1 when ctx2 is on top
    with pytest.raises(AssertionError):
        ctx1.pop()
    
    # State should not be corrupted - ctx2 should still be accessible
    assert _cv_app.get() == ctx2  # This fails - context var is empty
    
    # Test RequestContext
    environ = {
        'REQUEST_METHOD': 'GET',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'PATH_INFO': '/',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'http',
        'wsgi.input': sys.stdin,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False
    }
    
    rctx1 = app1.request_context(environ)
    environ2 = environ.copy()
    environ2['PATH_INFO'] = '/other'
    rctx2 = app1.request_context(environ2)
    
    rctx1.push()
    rctx2.push()
    
    with pytest.raises(AssertionError):
        rctx1.pop()
    
    assert _cv_request.get() == rctx2  # This fails - context var is empty
```

**Failing input**: Attempting to pop contexts in wrong order (ctx1.pop() when ctx2 is on top)

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
except AssertionError as e:
    print(f"AssertionError raised: {e}")

try:
    current = _cv_app.get()
    print(f"Context still available: {current}")
except LookupError:
    print("BUG: Context variable is empty after failed pop!")

try:
    ctx2.pop()
    print("ctx2 popped successfully")
except LookupError as e:
    print(f"BUG: Cannot pop ctx2: {e}")
```

## Why This Is A Bug

Both AppContext.pop() and RequestContext.pop() have the same flaw in their implementation:

1. They first remove tokens from `self._cv_tokens` 
2. Call `_cv_app.reset()` or `_cv_request.reset()` which clears the context variable
3. Only then check if the correct context is being popped
4. Raise AssertionError if wrong, but the context variable is already corrupted

This violates the principle of atomicity - the operation should either succeed completely or fail completely without side effects. The current implementation fails but leaves the system in an inconsistent state.

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

@@ -396,6 +398,10 @@ class RequestContext:
                 request_close()
         finally:
             ctx = _cv_request.get()
+            if ctx is not self:
+                raise AssertionError(
+                    f"Popped wrong request context. ({ctx!r} instead of {self!r})"
+                )
             token, app_ctx = self._cv_tokens.pop()
             _cv_request.reset(token)
 
@@ -406,10 +412,6 @@ class RequestContext:
             if app_ctx is not None:
                 app_ctx.pop(exc)
 
-            if ctx is not self:
-                raise AssertionError(
-                    f"Popped wrong request context. ({ctx!r} instead of {self!r})"
-                )
-
     def __enter__(self) -> RequestContext:
         self.push()
```