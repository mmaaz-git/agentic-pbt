import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse, urlencode
from requests_oauthlib.compliance_fixes import slack_compliance_fix

# Check the actual behavior
session = Mock()
session.access_token = "test_token"
hooks = {}

def register_hook(name, func):
    hooks[name] = func

session.register_compliance_hook = register_hook
slack_compliance_fix(session)

# Test case: URL parameter with empty value
base_url = "https://slack.com/api/test"
existing_params = {'param1': ''}
url_with_params = base_url + "?" + urlencode(existing_params)

print(f"Original URL: {url_with_params}")

headers = {}
data = {"some_data": "value"}

# Apply the compliance fix
fixed_url, fixed_headers, fixed_data = hooks["protected_request"](url_with_params, headers, data)

print(f"Fixed URL: {fixed_url}")

# The URL looks correct, the issue is with parse_qs
# Let's check parse_qs behavior with keep_blank_values
parsed_default = parse_qs(urlparse(fixed_url).query)
parsed_keep_blank = parse_qs(urlparse(fixed_url).query, keep_blank_values=True)

print(f"\nparse_qs (default): {parsed_default}")
print(f"parse_qs (keep_blank_values=True): {parsed_keep_blank}")

# The compliance fix doesn't actually modify the URL, it just adds token to data
# So this is not a bug in the compliance fix, but rather a quirk of parse_qs
# The URL parameter IS preserved in the URL string itself

# Let's check if the actual URL string contains the parameter
if "param1=" in fixed_url:
    print("\n✓ The parameter 'param1=' IS present in the URL string")
    print("  The issue is that parse_qs() by default drops empty values")
    print("  This is not a bug in slack_compliance_fix")