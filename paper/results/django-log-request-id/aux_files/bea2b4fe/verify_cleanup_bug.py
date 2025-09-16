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
from log_request_id import local
from log_request_id.middleware import RequestIDMiddleware

print("Verifying the local.request_id cleanup bug...\n")
print("=" * 60)

def test_cleanup(log_requests_enabled):
    """Test if local.request_id is cleaned up properly."""
    factory = RequestFactory()
    request = factory.get('/')
    response = HttpResponse()
    middleware = RequestIDMiddleware(get_response=lambda r: response)
    
    # Clear any previous state
    if hasattr(local, 'request_id'):
        del local.request_id
    
    # Set up the test
    settings.LOG_REQUEST_ID_HEADER = 'HTTP_X_REQUEST_ID'
    request.META['HTTP_X_REQUEST_ID'] = 'test-id-123'
    
    if log_requests_enabled:
        settings.LOG_REQUESTS = True
    else:
        settings.LOG_REQUESTS = False
    
    # Process request - should set local.request_id
    middleware.process_request(request)
    print(f"After process_request: local.request_id = {local.request_id!r}")
    assert local.request_id == 'test-id-123'
    
    # Process response - should clean up local.request_id (but does it?)
    middleware.process_response(request, response)
    
    has_request_id = hasattr(local, 'request_id')
    print(f"After process_response: hasattr(local, 'request_id') = {has_request_id}")
    
    if has_request_id:
        print(f"                       local.request_id = {local.request_id!r}")
    
    # Clean up settings
    if hasattr(settings, 'LOG_REQUESTS'):
        delattr(settings, 'LOG_REQUESTS')
    
    return not has_request_id

print("\nTest 1: With LOG_REQUESTS=False")
print("-" * 40)
cleanup_works_without_logging = test_cleanup(log_requests_enabled=False)

print("\n\nTest 2: With LOG_REQUESTS=True")
print("-" * 40)
cleanup_works_with_logging = test_cleanup(log_requests_enabled=True)

print("\n" + "=" * 60)
print("RESULTS:")
print(f"  Cleanup with LOG_REQUESTS=False: {'✓ WORKS' if cleanup_works_without_logging else '✗ FAILS'}")
print(f"  Cleanup with LOG_REQUESTS=True:  {'✓ WORKS' if cleanup_works_with_logging else '✗ FAILS'}")

if not cleanup_works_without_logging:
    print("\n🐛 BUG CONFIRMED!")
    print("The middleware only cleans up local.request_id when LOG_REQUESTS=True")
    print("This causes request IDs to leak between requests when logging is disabled!")
    
    # Look at the source code to confirm
    print("\n" + "=" * 60)
    print("Source code analysis:")
    print("-" * 40)
    print("From middleware.py lines 48-61:")
    print("""
    def process_response(self, request, response):
        ...
        if not getattr(settings, LOG_REQUESTS_SETTING, False):
            return response    # <-- Returns early without cleanup!
        ...
        try:
            del local.request_id   # <-- Cleanup only happens here
        except AttributeError:
            pass
        
        return response
    """)
    print("\nThe cleanup code is INSIDE the LOG_REQUESTS check,")
    print("so it only runs when logging is enabled!")
else:
    print("\nNo bug found - cleanup works correctly.")