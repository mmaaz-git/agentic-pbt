#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')
sys.path.insert(0, '/root/hypothesis-llm/worker_/14')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
import django
django.setup()

from django.test import RequestFactory
from django.conf import settings
from unittest import mock
from log_request_id.middleware import RequestIDMiddleware
from django.http import HttpResponse

print("=== Checking if middleware can receive non-ASCII request IDs ===")

factory = RequestFactory()

# Scenario 1: Non-ASCII ID from external header
print("\n1. External system sends non-ASCII request ID in header:")
with mock.patch.object(settings, 'LOG_REQUEST_ID_HEADER', 'HTTP_X_REQUEST_ID'):
    with mock.patch.object(settings, 'REQUEST_ID_RESPONSE_HEADER', 'X-Request-ID'):
        middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
        
        request = factory.get('/')
        # External system sends a request with non-ASCII ID
        request.META['HTTP_X_REQUEST_ID'] = 'req-Ā-123'
        
        middleware.process_request(request)
        print(f"   Received ID from header: {repr(request.id)}")
        
        response = HttpResponse()
        try:
            result = middleware.process_response(request, response)
            print(f"   Response header value: {repr(result['X-Request-ID'])}")
            print(f"   IDs match? {result['X-Request-ID'] == request.id}")
        except Exception as e:
            print(f"   Error setting response header: {e}")

# Scenario 2: Check if _generate_id can produce non-ASCII
print("\n2. Checking if _generate_id() can produce non-ASCII:")
middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
for _ in range(100):
    generated_id = middleware._generate_id()
    if not generated_id.isascii():
        print(f"   Found non-ASCII ID: {repr(generated_id)}")
        break
else:
    print("   All generated IDs are ASCII (as expected from uuid.uuid4().hex)")

print("\n=== Conclusion ===")
print("The middleware can receive non-ASCII request IDs from external systems")
print("via headers, which then get mangled when echoed back in response headers.")
print("This breaks request tracing/correlation across services.")