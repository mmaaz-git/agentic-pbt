# Bug Report: log_request_id.middleware Non-ASCII Request ID Mangling

**Target**: `log_request_id.middleware.RequestIDMiddleware`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The RequestIDMiddleware mangles non-ASCII request IDs when setting them as response headers, breaking request tracing across services that use non-ASCII identifiers.

## Property-Based Test

```python
@given(st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()),
       st.text(min_size=1, max_size=50).filter(lambda x: x.replace('_', '').replace('-', '').isalnum()))
@settings(max_examples=50)
def test_response_header_property(response_header_name, request_id):
    factory = RequestFactory()
    
    with mock.patch.object(django_settings, 'REQUEST_ID_RESPONSE_HEADER', response_header_name):
        middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
        
        request = factory.get('/')
        request.id = request_id
        
        response = HttpResponse()
        result = middleware.process_response(request, response)
        
        assert result.has_header(response_header_name)
        assert result[response_header_name] == request_id
```

**Failing input**: `response_header_name='0', request_id='Ā'`

## Reproducing the Bug

```python
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')
sys.path.insert(0, '/root/hypothesis-llm/worker_/14')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
import django
django.setup()

from django.test import RequestFactory
from django.http import HttpResponse
from django.conf import settings
from unittest import mock
from log_request_id.middleware import RequestIDMiddleware

factory = RequestFactory()

with mock.patch.object(settings, 'LOG_REQUEST_ID_HEADER', 'HTTP_X_REQUEST_ID'):
    with mock.patch.object(settings, 'REQUEST_ID_RESPONSE_HEADER', 'X-Request-ID'):
        middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
        
        request = factory.get('/')
        request.META['HTTP_X_REQUEST_ID'] = 'req-Ā-123'
        
        middleware.process_request(request)
        response = HttpResponse()
        result = middleware.process_response(request, response)
        
        print(f"Original ID: {request.id}")
        print(f"Response header: {result['X-Request-ID']}")
        print(f"Match: {result['X-Request-ID'] == request.id}")
```

## Why This Is A Bug

When the middleware receives a request ID containing non-ASCII characters from an external system (via the configured header), it correctly stores and uses this ID internally. However, when echoing this ID back in the response header, Django's HTTP response handling applies RFC 2047 encoding to non-ASCII characters, transforming the ID from 'req-Ā-123' to '=?utf-8?q?req-=C4=80-123?='. This breaks request correlation across services, as downstream systems receive a different ID than what was sent.

## Fix

```diff
--- a/log_request_id/middleware.py
+++ b/log_request_id/middleware.py
@@ -43,7 +43,10 @@ class RequestIDMiddleware(MiddlewareMixin):
 
     def process_response(self, request, response):
         if getattr(settings, REQUEST_ID_RESPONSE_HEADER_SETTING, False) and getattr(request, 'id', None):
-            response[getattr(settings, REQUEST_ID_RESPONSE_HEADER_SETTING)] = request.id
+            header_name = getattr(settings, REQUEST_ID_RESPONSE_HEADER_SETTING)
+            # Ensure request ID is ASCII-safe for HTTP headers
+            safe_id = request.id.encode('ascii', 'ignore').decode('ascii') if not request.id.isascii() else request.id
+            response[header_name] = safe_id
 
         if not getattr(settings, LOG_REQUESTS_SETTING, False):
             return response
```