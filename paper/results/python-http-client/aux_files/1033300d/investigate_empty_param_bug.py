#!/usr/bin/env python3
"""Investigate the empty query parameter value bug"""

import sys
from urllib.parse import parse_qs, urlparse, urlencode

sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from python_http_client.client import Client

# Test case that failed
params = {'0': ''}

client = Client(host='http://test')
url = client._build_url(params)

print(f"Input parameters: {params}")
print(f"Generated URL: {url}")
print(f"Expected: http://test?0=")
print()

# Parse the URL to see what happened
parsed = urlparse(url)
print(f"URL path: {parsed.path}")
print(f"URL query: {parsed.query}")
print(f"Parsed query params: {parse_qs(parsed.query)}")
print(f"Parsed query params (keep_blank_values=True): {parse_qs(parsed.query, keep_blank_values=True)}")
print()

# Test urllib's urlencode behavior directly
print("--- Testing urlencode directly ---")
test_params = [
    {'a': ''},
    {'a': 'value'},
    {'': 'value'},
    {'': ''},
    {'0': ''},
    {'key': '', 'key2': 'value'},
]

for p in test_params:
    # This is what the client uses
    encoded = urlencode(sorted(p.items()), True)
    print(f"Params: {p}")
    print(f"  urlencode(sorted(p.items()), True): {encoded}")
    print(f"  parse_qs(encoded): {parse_qs(encoded)}")
    print(f"  parse_qs(encoded, keep_blank_values=True): {parse_qs(encoded, keep_blank_values=True)}")
    print()

# More specific test
print("--- Specific behavior with empty values ---")
params_with_empty = {'key1': '', 'key2': 'value', 'key3': ''}
client2 = Client(host='http://example.com')
url2 = client2._build_url(params_with_empty)
print(f"Params: {params_with_empty}")
print(f"URL: {url2}")
parsed2 = urlparse(url2)
print(f"Query string: {parsed2.query}")
print(f"Parsed (default): {parse_qs(parsed2.query)}")
print(f"Parsed (keep_blank): {parse_qs(parsed2.query, keep_blank_values=True)}")