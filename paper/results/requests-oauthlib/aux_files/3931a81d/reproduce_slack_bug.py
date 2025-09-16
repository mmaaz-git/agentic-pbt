import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse, urlencode
from requests_oauthlib.compliance_fixes import slack_compliance_fix

# Minimal reproduction of the bug
session = Mock()
session.access_token = "test_token"
hooks = {}

def register_hook(name, func):
    hooks[name] = func

session.register_compliance_hook = register_hook
slack_compliance_fix(session)

# Test case that fails: URL parameter with empty value
base_url = "https://slack.com/api/test"
existing_params = {'param1': ''}  # Empty value parameter
url_with_params = base_url + "?" + urlencode(existing_params)

print(f"Original URL: {url_with_params}")
print(f"URL encoding of params: {urlencode(existing_params)}")

headers = {}
data = {"some_data": "value"}  # dict data

# Apply the compliance fix
fixed_url, fixed_headers, fixed_data = hooks["protected_request"](url_with_params, headers, data)

print(f"\nFixed URL: {fixed_url}")
print(f"Fixed data: {fixed_data}")

# Parse the fixed URL
parsed_url = urlparse(fixed_url)
query_params = parse_qs(parsed_url.query)

print(f"\nParsed query params: {query_params}")

# Check if the original parameter is preserved
if 'param1' in query_params:
    print("✓ Parameter 'param1' is preserved")
else:
    print("✗ BUG: Parameter 'param1' with empty value is NOT preserved!")
    print("  This happens because urlencode() with empty values creates 'param1='")
    print("  but parse_qs() by default ignores empty values")

# Second test: Multiple parameters, some with empty values
print("\n--- Test 2: Multiple parameters ---")
existing_params2 = {'param1': '', 'param2': 'value2', 'param3': ''}
url_with_params2 = base_url + "?" + urlencode(existing_params2)
print(f"Original URL: {url_with_params2}")

fixed_url2, _, _ = hooks["protected_request"](url_with_params2, headers, data)
parsed_url2 = urlparse(fixed_url2)
query_params2 = parse_qs(parsed_url2.query)

print(f"Parsed query params: {query_params2}")
for key in existing_params2:
    if key in query_params2:
        print(f"✓ Parameter '{key}' is preserved")
    else:
        print(f"✗ Parameter '{key}' is NOT preserved")