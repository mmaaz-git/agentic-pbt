#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=['log_request_id'],
    LOG_REQUESTS=False,  # Logging disabled - this is the key!
    LOG_REQUEST_ID_HEADER='HTTP_X_REQUEST_ID',
    NO_REQUEST_ID='none',  # Default value
)

import django
django.setup()

from django.test import RequestFactory
from django.http import HttpResponse
from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware
from log_request_id.filters import RequestIDFilter
import logging

print("Testing RequestIDFilter pollution between requests\n")
print("=" * 60)

factory = RequestFactory()
middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())
filter_obj = RequestIDFilter()

# Scenario: Logging that happens AFTER a request but BEFORE the next one
print("Scenario: Background task logging after request completes\n")

# Clear any existing state
if hasattr(local, 'request_id'):
    del local.request_id

# Create a log record BEFORE any request (should use default)
log_record = logging.LogRecord(
    name='test', level=logging.INFO, pathname='', lineno=0,
    msg='Background task before any request', args=(), exc_info=None
)
filter_obj.filter(log_record)
print(f"1. Before any request:")
print(f"   Log record request_id: {log_record.request_id!r} (should be 'none')")

# Process a request
request = factory.get('/api/endpoint')
request.META['HTTP_X_REQUEST_ID'] = 'api-request-789'
middleware.process_request(request)
print(f"\n2. During request:")
print(f"   local.request_id: {local.request_id!r}")

# Log something during the request
log_record2 = logging.LogRecord(
    name='test', level=logging.INFO, pathname='', lineno=0,
    msg='During request processing', args=(), exc_info=None
)
filter_obj.filter(log_record2)
print(f"   Log record request_id: {log_record2.request_id!r}")

# Complete the request
response = HttpResponse()
middleware.process_response(request, response)

# Now try to log something AFTER the request (e.g., background task)
log_record3 = logging.LogRecord(
    name='test', level=logging.INFO, pathname='', lineno=0,
    msg='Background task after request', args=(), exc_info=None
)
filter_obj.filter(log_record3)
print(f"\n3. After request completes (background task):")
print(f"   Log record request_id: {log_record3.request_id!r}")
print(f"   Expected: 'none' (default)")
print(f"   Actual: {log_record3.request_id!r}")

print("\n" + "=" * 60)
if log_record3.request_id == 'none':
    print("✓ Correct - background task uses default request_id")
else:
    print("🐛 BUG CONFIRMED!")
    print(f"Background task incorrectly uses request_id from previous request!")
    print(f"This causes log messages from background tasks to be")
    print(f"incorrectly associated with the last processed request.")
    print(f"\nThe bug occurs because:")
    print(f"1. Middleware doesn't clean up local.request_id when LOG_REQUESTS=False")
    print(f"2. RequestIDFilter uses the stale value for all subsequent logging")
    print(f"3. This affects any logging that happens outside request context")