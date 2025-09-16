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

print("=== Understanding Header Usage ===")
factory = RequestFactory()

# Test 1: Using the META key directly (as in the library's tests)
print("\n1. Using META key directly (REQUEST_ID_HEADER):")
with mock.patch.object(settings, 'LOG_REQUEST_ID_HEADER', 'REQUEST_ID_HEADER'):
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    request = factory.get('/')
    request.META['REQUEST_ID_HEADER'] = 'direct_meta_value'
    
    middleware.process_request(request)
    print(f"   request.META['REQUEST_ID_HEADER'] = 'direct_meta_value'")
    print(f"   Result: request.id = '{request.id}'")
    print(f"   Works: {request.id == 'direct_meta_value'}")

# Test 2: Using HTTP_ prefixed key
print("\n2. Using HTTP_ prefixed key:")
with mock.patch.object(settings, 'LOG_REQUEST_ID_HEADER', 'HTTP_X_REQUEST_ID'):
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    request = factory.get('/')
    request.META['HTTP_X_REQUEST_ID'] = 'http_prefixed_value'
    
    middleware.process_request(request)
    print(f"   request.META['HTTP_X_REQUEST_ID'] = 'http_prefixed_value'")
    print(f"   Result: request.id = '{request.id}'")
    print(f"   Works: {request.id == 'http_prefixed_value'}")

print("\n=== Conclusion ===")
print("The LOG_REQUEST_ID_HEADER setting expects the full META key name,")
print("not just the HTTP header name. For HTTP headers, this includes the 'HTTP_' prefix.")
print("This is actually the expected behavior, not a bug!")