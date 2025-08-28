"""
Reproduction script for OAuth1Session.authorization_url bug
Bug: None values are converted to string 'None' in URLs
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib import OAuth1Session

# Minimal reproduction
session = OAuth1Session('client_key', client_secret='secret')
session._client.client.resource_owner_key = None

# When request_token is None and resource_owner_key is also None,
# the URL should either omit the oauth_token parameter or handle it properly
url = session.authorization_url('https://example.com/auth', request_token=None)

print(f"Generated URL: {url}")

# The bug: None is converted to string 'None'
if 'oauth_token=None' in url:
    print("BUG CONFIRMED: None value is converted to string 'None' in the URL")
    print("This would cause the OAuth provider to receive 'None' as the literal token value")
else:
    print("Bug not present or has been fixed")

# Additional test with extra parameters that are None
print("\n" + "="*60)
print("Testing with additional None parameters:")

url2 = session.authorization_url('https://example.com/auth', 
                                 request_token=None,
                                 extra_param=None,
                                 another_param='valid')

print(f"URL with extra None params: {url2}")

# Check how None values are handled
from urllib.parse import parse_qs, urlparse
parsed = urlparse(url2)
params = parse_qs(parsed.query)
print(f"Parsed parameters: {params}")

for key, values in params.items():
    for value in values:
        if value == 'None':
            print(f"BUG: Parameter '{key}' has string value 'None' instead of being omitted or handled properly")