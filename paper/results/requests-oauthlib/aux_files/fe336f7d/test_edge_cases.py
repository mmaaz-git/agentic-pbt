import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib import OAuth1Session
from requests_oauthlib.oauth1_session import urldecode, TokenMissing
import json

print("Testing Edge Cases for OAuth1Session")
print("="*60)

# Test 1: Empty oauth_token should raise TokenMissing
print("\nTest 1: Empty oauth_token handling")
try:
    session = OAuth1Session('client_key', client_secret='secret')
    # Try to set token without oauth_token
    session.token = {'oauth_token_secret': 'secret', 'oauth_verifier': 'verifier'}
    print("✗ Should have raised TokenMissing exception")
except TokenMissing as e:
    print("✓ Correctly raised TokenMissing for missing oauth_token")

# Test 2: What happens with empty string oauth_token?
print("\nTest 2: Empty string oauth_token")
try:
    session = OAuth1Session('client_key', client_secret='secret')
    session.token = {'oauth_token': ''}  # Empty string
    token = session.token
    print(f"Token with empty oauth_token: {token}")
    if 'oauth_token' in token and token['oauth_token'] == '':
        print("✓ Empty string oauth_token preserved")
except Exception as e:
    print(f"✗ Unexpected error: {e}")

# Test 3: Unicode handling in tokens
print("\nTest 3: Unicode in oauth tokens")
try:
    session = OAuth1Session('client_key', client_secret='secret')
    unicode_token = {'oauth_token': '🦄unicorn', 'oauth_token_secret': 'секрет'}
    session.token = unicode_token
    retrieved = session.token
    if retrieved['oauth_token'] == '🦄unicorn' and retrieved.get('oauth_token_secret') == 'секрет':
        print("✓ Unicode preserved correctly")
    else:
        print(f"✗ Unicode not preserved: {retrieved}")
except Exception as e:
    print(f"✗ Error with unicode: {e}")

# Test 4: urldecode with malformed input
print("\nTest 4: urldecode with various malformed inputs")

test_cases = [
    ("", "Empty string"),
    ("&&&", "Only ampersands"),
    ("key=", "Missing value"),
    ("=value", "Missing key"),
    ("key1=val1&key2", "Missing second value"),
    ("key==value", "Double equals"),
    ("key=val=ue", "Equals in value"),
    ("nullbyte\x00test=value", "Null byte in input"),
]

for input_str, description in test_cases:
    try:
        result = urldecode(input_str)
        print(f"  {description}: {result}")
    except Exception as e:
        print(f"  {description}: ERROR - {type(e).__name__}: {e}")

# Test 5: JSON fallback with edge cases
print("\nTest 5: urldecode JSON fallback edge cases")

json_tests = [
    ('{"key": null}', "JSON with null"),
    ('{"": "empty_key"}', "JSON with empty key"),
    ('[]', "Empty JSON array"),
    ('null', "JSON null"),
    ('true', "JSON boolean true"),
    ('123', "JSON number"),
    ('"string"', "JSON string"),
    ('{"a":1, "a":2}', "Duplicate keys in JSON"),
]

for json_str, description in json_tests:
    try:
        result = urldecode(json_str)
        print(f"  {description}: {result} (type: {type(result)})")
    except Exception as e:
        print(f"  {description}: ERROR - {type(e).__name__}: {e}")

# Test 6: Very long tokens
print("\nTest 6: Very long token values")
try:
    session = OAuth1Session('client_key', client_secret='secret')
    long_token = 'a' * 10000
    session.token = {'oauth_token': long_token}
    retrieved = session.token
    if retrieved['oauth_token'] == long_token:
        print(f"✓ Long token (10000 chars) preserved")
    else:
        print(f"✗ Long token not preserved correctly")
except Exception as e:
    print(f"✗ Error with long token: {e}")

# Test 7: Token with all possible oauth fields
print("\nTest 7: Token property completeness")
session = OAuth1Session('client_key', client_secret='secret')
# Set all fields
session._client.client.resource_owner_key = 'key1'
session._client.client.resource_owner_secret = 'secret1'
session._client.client.verifier = 'verifier1'

token = session.token
print(f"Token with all fields: {token}")
expected_fields = ['oauth_token', 'oauth_token_secret', 'oauth_verifier']
for field in expected_fields:
    if field not in token:
        print(f"✗ Missing field: {field}")

# Test 8: authorization_url with None request_token
print("\nTest 8: authorization_url with None request_token and no resource_owner_key")
session = OAuth1Session('client_key', client_secret='secret')
# Clear any existing resource_owner_key
session._client.client.resource_owner_key = None
url = session.authorization_url('https://example.com/auth', request_token=None)
print(f"URL with None token: {url}")
if 'oauth_token=None' in url:
    print("✗ BUG FOUND: None is converted to string 'None' in URL")
elif 'oauth_token=' not in url:
    print("✓ oauth_token parameter omitted when None")
else:
    print(f"? Unexpected behavior in URL")

# Test 9: Double setting of token
print("\nTest 9: Setting token multiple times")
session = OAuth1Session('client_key', client_secret='secret')
token1 = {'oauth_token': 'token1', 'oauth_token_secret': 'secret1'}
token2 = {'oauth_token': 'token2', 'oauth_verifier': 'verifier2'}

session.token = token1
print(f"After first set: {session.token}")
session.token = token2
print(f"After second set: {session.token}")
# Check if oauth_token_secret is preserved or cleared
if 'oauth_token_secret' in session.token:
    print("Note: oauth_token_secret preserved from first set")
else:
    print("Note: oauth_token_secret cleared by second set")