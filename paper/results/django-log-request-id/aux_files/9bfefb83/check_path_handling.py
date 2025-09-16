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

print("=== Testing path handling with control characters ===")
factory = RequestFactory()
middleware = RequestIDMiddleware(get_response=lambda request: HttpResponse())

test_cases = [
    ('/normal/path', 'Normal path'),
    ('/path\nwith\nnewlines', 'Path with newlines'),
    ('/path\twith\ttabs', 'Path with tabs'),
    ('/path\rwith\rcarriage\rreturns', 'Path with carriage returns'),
    ('/path with spaces', 'Path with spaces'),
]

for path, description in test_cases:
    request = factory.get(path)
    response = HttpResponse(status=200)
    
    log_message = middleware.get_log_message(request, response)
    
    print(f"\n{description}:")
    print(f"  Original: {repr(path)}")
    print(f"  request.path: {repr(request.path)}")
    print(f"  Log message: {repr(log_message)}")
    
    # Check if the log message preserves the control characters
    if '\n' in path and '\n' in log_message:
        print("  WARNING: Newline preserved in log - could break single-line log parsers")
    if '\r' in path and '\r' in log_message:
        print("  WARNING: Carriage return preserved - could cause log injection")