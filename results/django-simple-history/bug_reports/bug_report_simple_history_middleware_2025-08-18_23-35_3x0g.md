# Bug Report: simple_history.middleware Nested Context Manager Bug

**Target**: `simple_history.middleware._context_manager`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_context_manager` function in django-simple-history doesn't properly handle nested contexts, causing outer context to be lost when inner context exits.

## Property-Based Test

```python
@given(
    nested_depth=st.integers(min_value=1, max_value=5)
)
def test_nested_context_managers(nested_depth):
    """Test that nested context managers don't interfere with each other"""
    requests = [Mock() for _ in range(nested_depth)]
    for i, req in enumerate(requests):
        req.id = i
    
    def nested_test(depth, remaining_requests):
        if not remaining_requests:
            assert hasattr(HistoricalRecords.context, 'request')
            assert HistoricalRecords.context.request.id == depth - 1
            return
        
        current_request = remaining_requests[0]
        with _context_manager(current_request):
            assert HistoricalRecords.context.request is current_request
            nested_test(depth, remaining_requests[1:])
            assert HistoricalRecords.context.request is current_request
    
    nested_test(nested_depth, requests)
```

**Failing input**: `nested_depth=2`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from simple_history.middleware import _context_manager
from simple_history.models import HistoricalRecords

request1 = Mock()
request1.id = "outer"

request2 = Mock()
request2.id = "inner"

with _context_manager(request1):
    print(f"Outer context: {HistoricalRecords.context.request.id}")
    
    with _context_manager(request2):
        print(f"Inner context: {HistoricalRecords.context.request.id}")
    
    print(f"Back to outer: {HistoricalRecords.context.request.id}")
```

## Why This Is A Bug

The context manager unconditionally deletes the request attribute when exiting, rather than restoring the previous value. This breaks the expected behavior of nested context managers where the outer context should be restored after the inner context exits. This could affect Django applications using nested middleware calls or recursive view calls that rely on the request context being properly maintained.

## Fix

```diff
--- a/simple_history/middleware.py
+++ b/simple_history/middleware.py
@@ -8,11 +8,14 @@ from .models import HistoricalRecords
 
 @contextmanager
 def _context_manager(request):
+    old_request = getattr(HistoricalRecords.context, 'request', None)
+    has_old_request = hasattr(HistoricalRecords.context, 'request')
     HistoricalRecords.context.request = request
 
     try:
         yield None
     finally:
-        try:
-            del HistoricalRecords.context.request
-        except AttributeError:
-            pass
+        if has_old_request:
+            HistoricalRecords.context.request = old_request
+        else:
+            try:
+                del HistoricalRecords.context.request
+            except AttributeError:
+                pass
```