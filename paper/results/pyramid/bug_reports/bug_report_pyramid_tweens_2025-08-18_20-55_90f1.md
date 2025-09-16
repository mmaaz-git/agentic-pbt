# Bug Report: pyramid.tweens._error_handler TypeError when called outside exception context

**Target**: `pyramid.tweens._error_handler`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `_error_handler` function in pyramid.tweens crashes with TypeError when called with an exception object outside of an active exception context, causing `sys.exc_info()` to return (None, None, None).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from unittest.mock import Mock
from pyramid.tweens import _error_handler
from pyramid.httpexceptions import HTTPNotFound
import pytest

@given(st.text(min_size=1, max_size=100))
def test_error_handler_reraises_on_httpnotfound(exc_message):
    """Test that _error_handler re-raises original exception when HTTPNotFound is raised."""
    request = Mock()
    request.invoke_exception_view = Mock(side_effect=HTTPNotFound())
    
    original_exc = ValueError(exc_message)
    
    with pytest.raises(ValueError) as exc_info:
        _error_handler(request, original_exc)
    
    assert str(exc_info.value) == exc_message
```

**Failing input**: `exc_message='0'` (any string triggers the bug)

## Reproducing the Bug

```python
import sys
from unittest.mock import Mock
from pyramid.tweens import _error_handler
from pyramid.httpexceptions import HTTPNotFound

request = Mock()
request.invoke_exception_view = Mock(side_effect=HTTPNotFound())

original_exc = ValueError("Test error")

try:
    _error_handler(request, original_exc)
except TypeError as e:
    print(f"TypeError: {e}")
```

## Why This Is A Bug

The `_error_handler` function is designed to handle exceptions and re-raise them if no exception view can handle them. However, it assumes it's always called from within an exception handling context. When called with an exception object directly (outside of an except block), `sys.exc_info()` returns `(None, None, None)`, which causes `reraise` to fail with `TypeError: 'NoneType' object is not callable` when it tries to execute `value = tp()` where `tp` is None.

## Fix

```diff
--- a/pyramid/tweens.py
+++ b/pyramid/tweens.py
@@ -6,7 +6,15 @@
 
 def _error_handler(request, exc):
     # NOTE: we do not need to delete exc_info because this function
     # should never be in the call stack of the exception
     exc_info = sys.exc_info()
+    
+    # If not called from an exception context, construct exc_info from the passed exception
+    if exc_info[0] is None:
+        exc_info = (type(exc), exc, exc.__traceback__)
 
     try:
         response = request.invoke_exception_view(exc_info)
```