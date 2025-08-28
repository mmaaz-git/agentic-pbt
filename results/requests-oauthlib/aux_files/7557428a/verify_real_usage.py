import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

import requests
from requests_oauthlib import OAuth1

print("Testing if these bugs can occur with real requests library usage:")
print("="*60)

# Check how requests handles headers
print("\n1. How requests handles headers:")
req = requests.Request('POST', 'http://example.com')
req.headers['Content-Type'] = b'\x80'  # Try setting bytes header
prepared = req.prepare()
print(f"Header type after prepare: {type(prepared.headers.get('Content-Type'))}")
print(f"Header value: {repr(prepared.headers.get('Content-Type'))}")

# Check how requests handles binary body
print("\n2. How requests handles binary body:")
req = requests.Request('POST', 'http://example.com', data=b'binary data')
prepared = req.prepare()
print(f"Body type: {type(prepared.body)}")
print(f"Body value: {prepared.body}")

# Test if OAuth1 would fail with real prepared request
print("\n3. Testing OAuth1 with binary body from real request:")
try:
    auth = OAuth1('client_key', 'client_secret')
    req = requests.Request('POST', 'http://example.com', data=b'')
    prepared = req.prepare()
    auth(prepared)
    print("SUCCESS: OAuth1 handled binary body correctly")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")

print("\n4. Testing OAuth1 with empty binary body and no Content-Type:")
try:
    auth = OAuth1('client_key', 'client_secret')
    req = requests.Request('POST', 'http://example.com', data=b'')
    prepared = req.prepare()
    # Remove Content-Type to trigger the extract_params check
    if 'Content-Type' in prepared.headers:
        del prepared.headers['Content-Type']
    auth(prepared)
    print("SUCCESS: OAuth1 handled empty binary body correctly")
except Exception as e:
    print(f"FAILURE: {type(e).__name__}: {e}")