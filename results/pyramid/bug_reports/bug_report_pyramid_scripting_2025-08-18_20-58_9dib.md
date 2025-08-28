# Bug Report: pyramid.scripting RequestContext Leak on Root Factory Exception

**Target**: `pyramid.scripting.prepare` and `pyramid.scripting.get_root`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When `prepare()` or `get_root()` encounters an exception from the root factory, the RequestContext is not properly cleaned up, leaving the request object in the threadlocal stack.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.scripting import prepare
from pyramid.threadlocal import get_current_request
from pyramid.config import Configurator
from pyramid.interfaces import IRootFactory

@given(st.text(min_size=1, max_size=50))
def test_prepare_cleans_up_on_root_factory_exception(error_msg):
    """Property: prepare should always clean up RequestContext, even on exception"""
    
    config = Configurator()
    registry = config.registry
    
    def failing_root_factory(request):
        raise ValueError(error_msg)
    
    registry.registerUtility(failing_root_factory, IRootFactory)
    
    try:
        initial_request = get_current_request()
    except:
        initial_request = None
    
    try:
        env = prepare(registry=registry)
    except ValueError:
        pass
    
    try:
        final_request = get_current_request()
    except:
        final_request = None
    
    # This assertion fails - request is leaked!
    assert final_request is initial_request, "RequestContext state not restored!"
```

**Failing input**: Any string value (e.g., `'0'`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.scripting import prepare
from pyramid.threadlocal import get_current_request
from pyramid.config import Configurator
from pyramid.interfaces import IRootFactory

config = Configurator()
registry = config.registry

def failing_root_factory(request):
    raise ValueError("Simulated failure")

registry.registerUtility(failing_root_factory, IRootFactory)

try:
    initial = get_current_request()
except:
    initial = None

try:
    env = prepare(registry=registry)
except ValueError:
    pass

leaked = get_current_request()
print(f"Request leaked: {leaked}")
print(f"Initial state: {initial}")
assert leaked is initial, "RequestContext was not cleaned up!"
```

## Why This Is A Bug

The functions `prepare()` and `get_root()` use a try-finally pattern to ensure cleanup via the `closer()` function, but this cleanup is only set up AFTER the root factory is called. If the root factory raises an exception, the code path at lines 99-100 (prepare) or lines 25-26 (get_root) calls `ctx.begin()` but never reaches the cleanup logic, leaving the RequestContext in an inconsistent state. This violates the principle that resources should be cleaned up even when exceptions occur.

## Fix

```diff
--- a/pyramid/scripting.py
+++ b/pyramid/scripting.py
@@ -96,23 +96,28 @@ def prepare(request=None, registry=None):
     # request.
     request.registry = registry
     ctx = RequestContext(request)
     ctx.begin()
-    apply_request_extensions(request)
-
-    def closer():
-        if request.finished_callbacks:
-            request._process_finished_callbacks()
-        ctx.end()
-
-    root_factory = registry.queryUtility(
-        IRootFactory, default=DefaultRootFactory
-    )
-    root = root_factory(request)
-    if getattr(request, 'context', None) is None:
-        request.context = root
-    return AppEnvironment(
-        root=root,
-        closer=closer,
-        registry=registry,
-        request=request,
-        root_factory=root_factory,
-    )
+    try:
+        apply_request_extensions(request)
+
+        def closer():
+            if request.finished_callbacks:
+                request._process_finished_callbacks()
+            ctx.end()
+
+        root_factory = registry.queryUtility(
+            IRootFactory, default=DefaultRootFactory
+        )
+        root = root_factory(request)
+        if getattr(request, 'context', None) is None:
+            request.context = root
+        return AppEnvironment(
+            root=root,
+            closer=closer,
+            registry=registry,
+            request=request,
+            root_factory=root_factory,
+        )
+    except:
+        ctx.end()
+        raise
```

Similar fix needed for `get_root()` at lines 24-32.