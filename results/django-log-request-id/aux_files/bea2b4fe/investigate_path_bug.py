import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

from django.conf import settings
settings.configure(
    DEBUG=True,
    SECRET_KEY='test',
    INSTALLED_APPS=['log_request_id'],
)

import django
django.setup()

from django.test import RequestFactory
from django.http import HttpResponse
from log_request_id.middleware import RequestIDMiddleware

print("Investigating path handling issue...\n")

factory = RequestFactory()

# Test various paths with special characters
test_paths = [
    '/#',
    '/#fragment',
    '/path#anchor',
    '/path?query=1#anchor',
    '/path with spaces',
    '/path%20encoded',
]

middleware = RequestIDMiddleware(get_response=lambda r: HttpResponse())

for path in test_paths:
    print(f"Original path: {path!r}")
    request = factory.get(path)
    print(f"Request.path:  {request.path!r}")
    
    response = HttpResponse()
    response.status_code = 200
    message = middleware.get_log_message(request, response)
    print(f"Log message:   {message}")
    print()

print("\n" + "="*50)
print("Analysis:")
print("The Django RequestFactory strips URL fragments (parts after #)")
print("This is correct HTTP behavior - fragments are client-side only.")
print("However, this means the log message doesn't match the input path.")
print("\nLet's check if there are any actual bugs with the middleware...")

# Check for actual bugs
print("\n" + "="*50)
print("Testing for actual bugs...")

# Test 1: Check if empty request ID causes issues
print("\n1. Testing empty request ID handling...")
request = factory.get('/')
settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
request.META['HTTP_X_REQUEST_ID'] = ''
middleware.process_request(request)
print(f"Empty header value -> request.id: {request.id!r}")
if request.id == '':
    print("✓ Empty request ID is preserved as-is")

# Test 2: Check whitespace-only request IDs
print("\n2. Testing whitespace-only request ID...")
request = factory.get('/')
request.META['HTTP_X_REQUEST_ID'] = '   '
middleware.process_request(request)
print(f"Whitespace header value -> request.id: {request.id!r}")
if request.id == '   ':
    print("✓ Whitespace request ID is preserved as-is")

# Test 3: Check very long request IDs
print("\n3. Testing very long request ID...")
long_id = 'a' * 10000
request = factory.get('/')
request.META['HTTP_X_REQUEST_ID'] = long_id
middleware.process_request(request)
print(f"Long ID (10000 chars) -> request.id length: {len(request.id)}")
if request.id == long_id:
    print("✓ Long request ID is preserved without truncation")