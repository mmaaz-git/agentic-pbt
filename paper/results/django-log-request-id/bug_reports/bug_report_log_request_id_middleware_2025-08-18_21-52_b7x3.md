# Bug Report: log_request_id.middleware Non-ASCII Header Name Crash

**Target**: `log_request_id.middleware.RequestIDMiddleware`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The RequestIDMiddleware crashes with UnicodeEncodeError when REQUEST_ID_RESPONSE_HEADER setting contains non-ASCII characters.

## Property-Based Test

```python
@given(st.text(min_size=1, max_size=50).filter(lambda x: not x.isascii()),
       st.text(min_size=1, max_size=50))
def test_non_ascii_header_name(response_header_name, request_id):
    factory = RequestFactory()
    
    with mock.patch.object(django_settings, 'REQUEST_ID_RESPONSE_HEADER', response_header_name):
        middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
        
        request = factory.get('/')
        request.id = request_id
        
        response = HttpResponse()
        result = middleware.process_response(request, response)
```

**Failing input**: `response_header_name='²', request_id='test'`

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

with mock.patch.object(settings, 'REQUEST_ID_RESPONSE_HEADER', '²'):
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    request = factory.get('/')
    request.id = 'test_id'
    
    response = HttpResponse()
    result = middleware.process_response(request, response)
```

## Why This Is A Bug

The middleware does not validate that the REQUEST_ID_RESPONSE_HEADER setting contains only ASCII characters, which are required for HTTP header names. When a non-ASCII character is used in the configuration, the middleware crashes with a UnicodeEncodeError instead of providing a clear configuration error at startup.

## Fix

```diff
--- a/log_request_id/middleware.py
+++ b/log_request_id/middleware.py
@@ -16,6 +16,11 @@ logger = logging.getLogger(__name__)
 
 class RequestIDMiddleware(MiddlewareMixin):
+    def __init__(self, get_response=None):
+        super().__init__(get_response)
+        header_name = getattr(settings, REQUEST_ID_RESPONSE_HEADER_SETTING, None)
+        if header_name and not header_name.isascii():
+            raise ValueError(f"REQUEST_ID_RESPONSE_HEADER must contain only ASCII characters, got: {header_name}")
+    
     def process_request(self, request):
         request_id = self._get_request_id(request)
         local.request_id = request_id
```