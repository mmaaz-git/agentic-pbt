import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib.oauth2_auth import OAuth2

# Minimal reproduction
token = {
    'access_token': 'test_token',
    'token_type': 'Bearer',
    '__class__': 'malicious_string'  # This special attribute causes the issue
}

try:
    oauth2 = OAuth2(client_id='test_client', token=token)
    print("OAuth2 object created successfully")
except TypeError as e:
    print(f"TypeError: {e}")
    print("\nThis happens because OAuth2.__init__ blindly sets all token")
    print("dictionary keys as attributes on the client object using setattr(),")
    print("including special attributes like '__class__' which have restrictions.")