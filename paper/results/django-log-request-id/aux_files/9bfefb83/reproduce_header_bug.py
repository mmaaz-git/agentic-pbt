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

# Bug 1: Header not being used when configured
print("=== Bug 1: Header-based ID not working correctly ===")
factory = RequestFactory()

# Configure to use header '0' (which should map to HTTP_0 in META)
with mock.patch.object(settings, 'LOG_REQUEST_ID_HEADER', '0'):
    middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())
    
    request = factory.get('/')
    # Set the header as Django would see it in META
    request.META['HTTP_0'] = 'test_id_value'
    
    middleware.process_request(request)
    
    print(f"Expected request.id: 'test_id_value'")
    print(f"Actual request.id: '{request.id}'")
    print(f"Bug confirmed: {request.id != 'test_id_value'}")
    
print("\n=== Issue Explanation ===")
print("The middleware's _get_request_id method expects headers to be in a specific META format.")
print("When LOG_REQUEST_ID_HEADER is set to '0', it tries to find request.META['0']")
print("But Django stores HTTP headers as request.META['HTTP_0']")
print("The middleware doesn't handle this transformation correctly.")