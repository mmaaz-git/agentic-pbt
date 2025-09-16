import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse, urlencode
from requests_oauthlib.compliance_fixes import instagram_compliance_fix

print("=== Instagram Compliance Fix Bug Investigation ===\n")

# Setup
session = Mock()
session.access_token = "session_token_123"
hooks = {}

def register_hook(name, func):
    hooks[name] = func

session.register_compliance_hook = register_hook
instagram_compliance_fix(session)

print("Test 1: URL parameters with empty values (no existing token)")
print("-" * 50)
base_url = "https://api.instagram.com/v1/users"
other_params = {'param1': ''}  # Empty value
url = base_url + "?" + urlencode(other_params)

print(f"Original URL: {url}")
headers = {}
data = None

fixed_url, _, _ = hooks["protected_request"](url, headers, data)
print(f"Fixed URL: {fixed_url}")

# Check with keep_blank_values
parsed_default = parse_qs(urlparse(fixed_url).query)
parsed_keep_blank = parse_qs(urlparse(fixed_url).query, keep_blank_values=True)

print(f"Parsed (default): {parsed_default}")
print(f"Parsed (keep_blank_values): {parsed_keep_blank}")

if 'param1' in parsed_keep_blank:
    print("✓ Parameter 'param1' is preserved (when using keep_blank_values)")
else:
    print("✗ BUG: Parameter 'param1' is NOT preserved")

print("\nTest 2: Existing token same as session token")
print("-" * 50)
# When the existing token in URL matches the session token
url_with_token = base_url + "?" + urlencode({'access_token': 'session_token_123'})
print(f"Original URL: {url_with_token}")
print(f"Session token: session_token_123")

fixed_url2, _, _ = hooks["protected_request"](url_with_token, headers, data)
print(f"Fixed URL: {fixed_url2}")

parsed2 = parse_qs(urlparse(fixed_url2).query)
print(f"Parsed params: {parsed2}")

# Analyze what happens
if 'access_token' in parsed2:
    tokens = parsed2['access_token']
    print(f"Access token(s) in URL: {tokens}")
    if len(tokens) == 1 and tokens[0] == 'session_token_123':
        print("✓ Only one token present (correct)")
    else:
        print(f"✗ Multiple tokens or wrong token: {tokens}")

print("\nTest 3: Different existing token")  
print("-" * 50)
url_with_diff_token = base_url + "?" + urlencode({'access_token': 'different_token_456'})
print(f"Original URL: {url_with_diff_token}")
print(f"Session token: session_token_123")

fixed_url3, _, _ = hooks["protected_request"](url_with_diff_token, headers, data)
print(f"Fixed URL: {fixed_url3}")

parsed3 = parse_qs(urlparse(fixed_url3).query)
print(f"Parsed params: {parsed3}")

if 'access_token' in parsed3:
    tokens = parsed3['access_token']
    print(f"Access token(s) in URL: {tokens}")
    if 'different_token_456' in tokens:
        print("✓ Original token preserved")
    if 'session_token_123' in tokens:
        print("✗ Session token incorrectly added")