import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

import requests
from requests_oauthlib import OAuth1

print("Investigating exactly when the bugs trigger:")
print("="*60)

# Bug 1: Content-Type header with non-UTF8 bytes
print("\n1. Testing Content-Type header bug with real requests:")
try:
    auth = OAuth1('client_key', 'client_secret')
    req = requests.Request('POST', 'http://example.com', data='test')
    prepared = req.prepare()
    # Force a bytes Content-Type header
    prepared.headers['Content-Type'] = b'\x80\x81\x82'
    auth(prepared)
    print("No error - unexpected!")
except UnicodeDecodeError as e:
    print(f"UnicodeDecodeError confirmed: {e}")

# Let's check what happens with various Content-Type values
print("\n2. Testing various Content-Type header values:")
test_values = [
    ('string', 'text/plain'),
    ('bytes utf8', b'text/plain'),
    ('bytes latin1', 'text/plain'.encode('latin-1')),
    ('bytes with high bits', b'\xc0\xfe'),
]

auth = OAuth1('client_key', 'client_secret')
for label, ct_value in test_values:
    try:
        req = requests.Request('POST', 'http://example.com', data='test')
        prepared = req.prepare()
        prepared.headers['Content-Type'] = ct_value
        auth(prepared)
        print(f"  {label}: SUCCESS")
    except Exception as e:
        print(f"  {label}: FAILED - {type(e).__name__}: {e}")

# Bug 2: Binary body triggering extract_params
print("\n3. When does extract_params get called on binary body?")
print("   extract_params is called when Content-Type is missing and body exists")

auth = OAuth1('client_key', 'client_secret')

test_cases = [
    ('Binary body with Content-Type', b'data', {'Content-Type': 'application/octet-stream'}),
    ('Binary body without Content-Type', b'data', {}),
    ('Empty binary body without Content-Type', b'', {}),
    ('String body without Content-Type', 'data', {}),
]

for label, body, headers in test_cases:
    try:
        req = requests.Request('POST', 'http://example.com')
        prepared = req.prepare()
        prepared.body = body
        prepared.headers.clear()
        prepared.headers.update(headers)
        auth(prepared)
        print(f"  {label}: SUCCESS")
    except Exception as e:
        print(f"  {label}: FAILED - {type(e).__name__}: {e}")