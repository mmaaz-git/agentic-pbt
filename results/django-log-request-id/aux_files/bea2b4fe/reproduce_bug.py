#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=['log_request_id'],
    LOG_REQUESTS=False,  # Logging disabled
)

import django
django.setup()

from django.test import RequestFactory
from django.http import HttpResponse
from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware

factory = RequestFactory()
middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())

# First request with ID 'request-1'
request1 = factory.get('/path1')
request1.META['HTTP_X_REQUEST_ID'] = 'request-1'
settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'

middleware.process_request(request1)
print(f"Request 1 - After process_request: local.request_id = {local.request_id!r}")

response1 = HttpResponse()
middleware.process_response(request1, response1)
print(f"Request 1 - After process_response: local.request_id = {local.request_id!r}")

# Second request with ID 'request-2'
request2 = factory.get('/path2')
request2.META['HTTP_X_REQUEST_ID'] = 'request-2'

middleware.process_request(request2)
print(f"Request 2 - After process_request: local.request_id = {local.request_id!r}")

# BUG: local.request_id should be 'request-2' but it's still 'request-1'
assert local.request_id == 'request-2', f"Expected 'request-2', got {local.request_id!r}"