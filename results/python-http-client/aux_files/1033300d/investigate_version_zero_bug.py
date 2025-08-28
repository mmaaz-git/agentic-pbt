#!/usr/bin/env python3
"""Investigate the version=0 bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from python_http_client.client import Client

print("=== Testing version=0 ===")
client0 = Client(host='http://test', version=0)
url0 = client0._build_url(None)
print(f"version=0: {client0._version}")
print(f"URL: {url0}")
print(f"Expected: http://test/v0")
print()

print("=== Testing other falsy values ===")
test_versions = [0, '', None, False, 0.0]

for v in test_versions:
    client = Client(host='http://test', version=v)
    url = client._build_url(None)
    print(f"version={v!r} (type: {type(v).__name__})")
    print(f"  _version attribute: {client._version!r}")
    print(f"  URL: {url}")
    print(f"  Has version in URL: {'/v' in url}")
    print()

print("=== Looking at the _build_url logic ===")
# Let's trace through the logic
client = Client(host='http://test', version=0)
print(f"client._version = {client._version!r}")
print(f"bool(client._version) = {bool(client._version)}")

# The issue is in line 132-135 of client.py:
#   if self._version:
#       url = self._build_versioned_url(url)
#   else:
#       url = '{}{}'.format(self.host, url)

print("\nThe bug: `if self._version:` treats 0 as False!")
print("This means version=0 is ignored, even though 0 is a valid version number.")

print("\n=== Testing the bug with different version values ===")
for v in [-1, 0, 1, 2, "0", "1", 0.0, 1.0]:
    client = Client(host='http://api.example.com', version=v, url_path=['users'])
    url = client._build_url({'id': '123'})
    print(f"version={v!r}: {url}")