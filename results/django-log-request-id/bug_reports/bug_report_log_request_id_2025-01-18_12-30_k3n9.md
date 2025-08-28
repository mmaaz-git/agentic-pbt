# Bug Report: log_request_id Thread-Local Pollution

**Target**: `log_request_id.middleware.RequestIDMiddleware`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The RequestIDMiddleware fails to clean up `local.request_id` when `LOG_REQUESTS=False`, causing request IDs to leak into subsequent logging outside of request contexts.

## Property-Based Test

```python
@given(st.text(min_size=1, max_size=50))
@hypo_settings(max_examples=50)
def test_local_cleanup_after_response(request_id):
    """local.request_id should be cleaned up after process_response."""
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse()
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    
    settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
    request.META['HTTP_X_REQUEST_ID'] = request_id
    
    middleware.process_request(request)
    assert local.request_id == request_id
    
    middleware.process_response(request, response)
    assert not hasattr(local, 'request_id'), "local.request_id not cleaned up after response"
```

**Failing input**: Any non-empty string value for `request_id`

## Reproducing the Bug

```python
from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=['log_request_id'],
    LOG_REQUESTS=False,
    LOG_REQUEST_ID_HEADER='HTTP_X_REQUEST_ID',
    NO_REQUEST_ID='none',
)

import django
django.setup()

from django.test import RequestFactory
from django.http import HttpResponse
from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware
from log_request_id.filters import RequestIDFilter
import logging

factory = RequestFactory()
middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
filter_obj = RequestIDFilter()

request = factory.get('/api/endpoint')
request.META['HTTP_X_REQUEST_ID'] = 'api-request-789'
middleware.process_request(request)

response = HttpResponse()
middleware.process_response(request, response)

log_record = logging.LogRecord(
    name='test', level=logging.INFO, pathname='', lineno=0,
    msg='Background task after request', args=(), exc_info=None
)
filter_obj.filter(log_record)

print(f"Log record request_id: {log_record.request_id}")
print(f"Expected: 'none'")
print(f"Actual: 'api-request-789'")
```

## Why This Is A Bug

This violates the expected isolation between requests and background tasks. When `LOG_REQUESTS=False`, the middleware returns early from `process_response()` without cleaning up `local.request_id`. This causes the RequestIDFilter to incorrectly associate log messages from background tasks or subsequent non-request contexts with the last processed request's ID instead of using the configured default.

## Fix

```diff
--- a/log_request_id/middleware.py
+++ b/log_request_id/middleware.py
@@ -44,10 +44,14 @@ class RequestIDMiddleware(MiddlewareMixin):
     def process_response(self, request, response):
         if getattr(settings, REQUEST_ID_RESPONSE_HEADER_SETTING, False) and getattr(request, 'id', None):
             response[getattr(settings, REQUEST_ID_RESPONSE_HEADER_SETTING)] = request.id
 
+        # Clean up local.request_id regardless of LOG_REQUESTS setting
+        try:
+            del local.request_id
+        except AttributeError:
+            pass
+
         if not getattr(settings, LOG_REQUESTS_SETTING, False):
             return response
 
         # Don't log favicon
         if 'favicon' in request.path:
@@ -55,11 +59,6 @@ class RequestIDMiddleware(MiddlewareMixin):
 
         logger.info(self.get_log_message(request, response))
 
-        try:
-            del local.request_id
-        except AttributeError:
-            pass
-
         return response
```