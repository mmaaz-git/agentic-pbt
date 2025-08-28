import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib import OAuth1Session
from urllib.parse import urlencode

# Test case 1: Round-trip with special characters in keys
print("Test 1: Special character ':' in parameter key")
session = OAuth1Session('client_key', client_secret='secret')

# Create params with special character in key
params = {':': 'value1', 'oauth_token': 'test_token'}
url = f"https://example.com/callback?{urlencode(params)}"
print(f"Input URL: {url}")

parsed = session.parse_authorization_response(url)
print(f"Parsed result: {parsed}")

# The key should be preserved
if ':' in parsed:
    print("✓ Special character key preserved in parsing")
else:
    print("✗ Special character key NOT preserved")

print("\n" + "="*50 + "\n")

# Test case 2: URL encoding consistency
print("Test 2: Space encoding in authorization_url")
session2 = OAuth1Session('client_key', client_secret='secret')

# Token with space
token_with_space = ' token '
auth_url = session2.authorization_url('https://api.example.com/authorize', 
                                      request_token=token_with_space,
                                      custom_param=' value ')
print(f"Generated URL: {auth_url}")

# Parse it back
from urllib.parse import parse_qs, urlparse
parsed_url = urlparse(auth_url)
params = parse_qs(parsed_url.query)
print(f"Parsed params: {params}")

# Check if spaces are preserved after round-trip
if 'oauth_token' in params and params['oauth_token'][0] == token_with_space:
    print("✓ Spaces preserved in oauth_token")
else:
    print(f"✗ Spaces NOT preserved: got {params.get('oauth_token', ['NOT FOUND'])}")

print("\n" + "="*50 + "\n")

# Test case 3: Complex round-trip
print("Test 3: Full round-trip with edge cases")
session3 = OAuth1Session('client_key', client_secret='secret')

# Edge case parameters
edge_params = {
    'oauth_token': 'token123',
    'oauth_token_secret': 'secret456',
    'oauth_verifier': 'verifier789',
    'special:key': 'value',
    'key_with_space': ' space value '
}

# Create URL
callback_url = f"https://example.com/callback?{urlencode(edge_params)}"
print(f"Callback URL: {callback_url}")

# Parse it
parsed = session3.parse_authorization_response(callback_url)
print(f"Parsed: {parsed}")

# Check token property
token = session3.token
print(f"Token property: {token}")

# Verify oauth fields are preserved
oauth_fields = ['oauth_token', 'oauth_token_secret', 'oauth_verifier']
for field in oauth_fields:
    if field in edge_params:
        if field in token and token[field] == edge_params[field]:
            print(f"✓ {field} preserved correctly")
        else:
            print(f"✗ {field} NOT preserved correctly: expected {edge_params[field]}, got {token.get(field, 'NOT FOUND')}")