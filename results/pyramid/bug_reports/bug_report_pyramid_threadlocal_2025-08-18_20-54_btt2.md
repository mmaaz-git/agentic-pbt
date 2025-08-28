# Bug Report: pyramid.threadlocal KeyError in get_current_request/get_current_registry

**Target**: `pyramid.threadlocal`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`get_current_request()` and `get_current_registry()` raise KeyError when the manager stack contains items without 'request' or 'registry' keys, instead of gracefully returning None or the default registry.

## Property-Based Test

```python
@given(st.lists(st.dictionaries(st.text(), st.text()), min_size=1))
def test_request_context_begin_end_explicit(items):
    mock_request = Mock()
    mock_request.registry = items[0]
    
    # Push items without 'request' key to manager
    for item in items:
        manager.push({"item": item})
    
    ctx = RequestContext(mock_request)
    ctx.begin()
    ctx.end()
    
    # This should return None but raises KeyError
    assert get_current_request() is None
```

**Failing input**: `items=[{}]`

## Reproducing the Bug

```python
from pyramid.threadlocal import manager, get_current_request, get_current_registry

manager.clear()
manager.push({"foo": "bar"})

result = get_current_request()
```

## Why This Is A Bug

The docstring for `get_current_request()` states it should "Return the currently active request or ``None`` if no request is currently active." Instead, it raises KeyError when stack items lack a 'request' key. This violates the documented contract and makes the functions fragile to stack pollution from other code using the manager.

## Fix

```diff
--- a/pyramid/threadlocal.py
+++ b/pyramid/threadlocal.py
@@ -51,7 +51,7 @@ def get_current_request():
     tested nor scripted.
 
     """
-    return manager.get()['request']
+    return manager.get().get('request', None)
 
 
 def get_current_registry(
@@ -68,4 +68,5 @@ def get_current_registry(
     tested nor scripted.
 
     """
-    return manager.get()['registry']
+    from pyramid.registry import global_registry
+    return manager.get().get('registry', global_registry)
```