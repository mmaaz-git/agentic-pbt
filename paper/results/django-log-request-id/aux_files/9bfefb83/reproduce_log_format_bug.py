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
from log_request_id.middleware import RequestIDMiddleware

print("=== Bug: Log message format breaks with newlines in path ===")
factory = RequestFactory()
middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())

# Create a request with a newline in the path
request = factory.get('/test\npath')
response = HttpResponse(status=200)

log_message = middleware.get_log_message(request, response)

print(f"Path with newline: '/test\\npath'")
print(f"Generated log message:")
print(repr(log_message))
print()
print("Expected format: 'method=GET path=/test\\npath status=200'")
print(f"Actual output: {repr(log_message)}")
print()
print("Issue: The newline in the path creates a multi-line log message,")
print("which can break log parsing tools that expect single-line entries.")
print("This is a security/reliability issue - paths with control characters")
print("should be escaped or sanitized in logs.")