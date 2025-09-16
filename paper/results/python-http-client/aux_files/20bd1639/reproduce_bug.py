import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

import python_http_client.client as client

# Create a client with an empty host
c = client.Client(host='')

# Build URL with a query parameter that has a colon in the key
url = c._build_url({':': ''})

print(f"Generated URL: {url}")
print(f"Query parameter key ':' in URL: {':' in url}")
print(f"Encoded form '%3A' in URL: {'%3A' in url}")

# The issue: the colon is URL-encoded to %3A, but the original test
# was checking if the raw key appears in the URL