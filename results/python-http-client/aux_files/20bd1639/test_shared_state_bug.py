import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

import python_http_client.client as client

# Test if headers are shared between client instances
headers = {"Authorization": "Bearer token"}
c1 = client.Client(host="http://example.com", request_headers=headers)

# Create a child client
c2 = c1._("api")

print(f"c1 headers before update: {c1.request_headers}")
print(f"c2 headers before update: {c2.request_headers}")
print(f"Are they the same object? {c1.request_headers is c2.request_headers}")

# Update headers on c2
c2._update_headers({"X-Custom": "value"})

print(f"\nc1 headers after c2 update: {c1.request_headers}")
print(f"c2 headers after c2 update: {c2.request_headers}")

# This is a bug! Updating c2's headers also modified c1's headers
# because they share the same dictionary object