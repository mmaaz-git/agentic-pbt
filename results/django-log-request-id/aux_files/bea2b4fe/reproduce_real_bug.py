#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=['log_request_id'],
    LOG_REQUESTS=False,  # Logging disabled
    LOG_REQUEST_ID_HEADER='HTTP_X_REQUEST_ID',
    NO_REQUEST_ID='NO-ID',  # Custom default
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

print("Demonstrating the thread-local pollution bug:\n")
print("=" * 60)

# First request WITH a request ID
request1 = factory.get('/path1')
request1.META['HTTP_X_REQUEST_ID'] = 'explicit-id-123'

middleware.process_request(request1)
print(f"Request 1 (with header): local.request_id = {local.request_id!r}")

response1 = HttpResponse()
middleware.process_response(request1, response1)
print(f"After response 1: local.request_id = {local.request_id!r}\n")

# Second request WITHOUT a request ID header (should use default)
request2 = factory.get('/path2')
# No header set!

middleware.process_request(request2)
print(f"Request 2 (no header): request.id = {request2.id!r}")
print(f"                      local.request_id = {local.request_id!r}")

# Now test the filter - it will use the polluted local.request_id!
filter_obj = RequestIDFilter()
log_record = logging.LogRecord(
    name='test', level=logging.INFO, pathname='', lineno=0,
    msg='Test message', args=(), exc_info=None
)
filter_obj.filter(log_record)

print(f"\nLog record request_id: {log_record.request_id!r}")
print(f"Expected: 'NO-ID' (the configured default)")
print(f"Actual: {log_record.request_id!r}")

print("\n" + "=" * 60)
if log_record.request_id == 'NO-ID':
    print("✓ No bug - correct default used")
else:
    print("🐛 BUG CONFIRMED!")
    print("The RequestIDFilter is using the leftover request_id from")
    print("the previous request instead of the configured default!")
    print("\nThis happens because:")
    print("1. First request sets local.request_id = 'explicit-id-123'")
    print("2. process_response doesn't clean it up (LOG_REQUESTS=False)")
    print("3. Second request uses default 'NO-ID' for request.id")
    print("4. But local.request_id still has the old value!")
    print("5. RequestIDFilter uses the polluted local.request_id")