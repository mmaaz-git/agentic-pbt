import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib import OAuth1
from unittest.mock import Mock

print("Bug 1: UnicodeDecodeError with non-UTF8 Content-Type header")
print("=" * 60)
try:
    oauth = OAuth1(client_key='test_key')
    request = Mock()
    request.url = "http://example.com"
    request.method = "POST"
    request.body = "key=value"
    request.headers = {"Content-Type": b'\x80'}  # Non-UTF8 bytes
    request.prepare_headers = Mock()
    
    result = oauth(request)
    print("No error - unexpected!")
except UnicodeDecodeError as e:
    print(f"UnicodeDecodeError: {e}")
    print("Bug confirmed: Content-Type header with non-UTF8 bytes causes crash")

print("\n" + "="*60)
print("Bug 2: TypeError with binary body")
print("=" * 60)
try:
    oauth = OAuth1(client_key='test_key')
    request = Mock()
    request.url = "http://example.com"
    request.method = "POST"
    request.body = b''  # Binary body
    request.headers = {}
    request.prepare_headers = Mock()
    
    result = oauth(request)
    print("No error - unexpected!")
except TypeError as e:
    print(f"TypeError: {e}")
    print("Bug confirmed: Binary body causes TypeError in extract_params")

print("\n" + "="*60)
print("Bug 3: Non-string signature_type crashes")
print("=" * 60)
try:
    oauth = OAuth1(client_key='test_key', signature_type=123)
    print(f"OAuth created with signature_type: {oauth.client.signature_type}")
    print("No crash - this is handled correctly")
except Exception as e:
    print(f"Error: {e}")
    print("Bug confirmed: Non-string signature_type causes error")