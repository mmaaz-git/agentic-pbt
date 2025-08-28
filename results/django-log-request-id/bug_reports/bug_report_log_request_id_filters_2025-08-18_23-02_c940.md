# Bug Report: log_request_id.filters Unhandled Exceptions in RequestIDFilter

**Target**: `log_request_id.filters.RequestIDFilter`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

RequestIDFilter.filter() crashes with unhandled exceptions when the local object's request_id attribute raises an exception during access, causing logging to fail entirely.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from log_request_id.filters import RequestIDFilter
from log_request_id import filters
import logging

@given(exception_msg=st.text(min_size=1))
def test_filter_handles_local_exceptions(exception_msg):
    """The filter should handle exceptions from local.request_id access gracefully."""
    
    class ProblematicLocal:
        @property
        def request_id(self):
            raise RuntimeError(exception_msg)
    
    original_local = filters.local
    filters.local = ProblematicLocal()
    
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py",
        lineno=1, msg="test", args=(), exc_info=None
    )
    
    try:
        result = filter_obj.filter(record)
        assert result is True
        assert hasattr(record, 'request_id')
    finally:
        filters.local = original_local
```

**Failing input**: Any access to `local.request_id` that raises an exception

## Reproducing the Bug

```python
from log_request_id.filters import RequestIDFilter
from log_request_id import filters
import logging

class ProblematicLocal:
    @property
    def request_id(self):
        raise RuntimeError("Database connection lost")

filters.local = ProblematicLocal()

filter_obj = RequestIDFilter()
record = logging.LogRecord(
    name="test", level=20, pathname="test.py", 
    lineno=1, msg="test", args=(), exc_info=None
)

filter_obj.filter(record)  # Raises RuntimeError
```

## Why This Is A Bug

The RequestIDFilter is a logging filter that should never prevent logging from working. When `local.request_id` raises an exception (which can happen in production when the local storage is customized or has issues), the entire logging pipeline fails. The filter should catch exceptions and fall back to the default value, ensuring logging continues to work even when request ID retrieval fails.

## Fix

```diff
--- a/log_request_id/filters.py
+++ b/log_request_id/filters.py
@@ -9,6 +9,11 @@ class RequestIDFilter(logging.Filter):
 
     def filter(self, record):
         default_request_id = getattr(settings, LOG_REQUESTS_NO_SETTING, DEFAULT_NO_REQUEST_ID)
-        record.request_id = getattr(local, 'request_id', default_request_id)
+        try:
+            record.request_id = getattr(local, 'request_id', default_request_id)
+        except Exception:
+            # If accessing local.request_id raises any exception,
+            # fall back to the default to ensure logging continues
+            record.request_id = default_request_id
         return True
```