#!/usr/bin/env python3
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

print("=== Bug 1: Non-ASCII header names cause UnicodeEncodeError ===")
factory = RequestFactory()

# Test with non-ASCII header name
with mock.patch.object(settings, 'REQUEST_ID_RESPONSE_HEADER', '²'):  # superscript 2
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    request = factory.get('/')
    request.id = 'test_id'
    
    response = HttpResponse()
    
    try:
        result = middleware.process_response(request, response)
        print("ERROR: Should have raised an exception!")
    except UnicodeEncodeError as e:
        print(f"Caught expected error: {e}")
        print("Issue: Non-ASCII header names are not validated")
        print("Impact: Server error when trying to set response headers")

print("\n=== Bug 2: Non-ASCII request IDs get mangled in response headers ===")

# Test with ASCII header name but non-ASCII request ID
with mock.patch.object(settings, 'REQUEST_ID_RESPONSE_HEADER', 'X-Request-ID'):
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    request = factory.get('/')
    request.id = 'Ā'  # Latin A with macron
    
    response = HttpResponse()
    result = middleware.process_response(request, response)
    
    print(f"Original request.id: {repr(request.id)}")
    print(f"Response header value: {repr(result['X-Request-ID'])}")
    print(f"Are they equal? {result['X-Request-ID'] == request.id}")
    print()
    print("Issue: Non-ASCII characters in the request ID get encoded")
    print("using RFC 2047 encoding (=?utf-8?b?...?=) when set as header values.")
    print("This changes the value and makes it unusable for correlation.")