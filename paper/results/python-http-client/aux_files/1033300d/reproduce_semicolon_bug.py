#!/usr/bin/env python3
"""Minimal reproduction of the semicolon query parameter issue"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from python_http_client.client import Client
from urllib.parse import unquote

# Test case that failed
host = 'http://0'
params = {';': ''}

client = Client(host=host)
url = client._build_url(params)

print(f"Input parameters: {params}")
print(f"Generated URL: {url}")
print(f"Expected semicolon in URL: ';' in url = {';' in url}")
print(f"Unquoted URL: {unquote(url)}")

# Let's also test other special characters
special_params = {
    ';': 'value1',
    '&': 'value2',
    '=': 'value3',
    '?': 'value4',
    '#': 'value5',
    '/': 'value6',
    ' ': 'value7',
}

print("\n--- Testing various special characters as keys ---")
for key, value in special_params.items():
    client = Client(host='http://test')
    url = client._build_url({key: value})
    print(f"Key: '{key}' -> URL: {url}")
    print(f"  Key in URL: {key in url}")
    print(f"  Key in unquoted URL: {key in unquote(url)}")