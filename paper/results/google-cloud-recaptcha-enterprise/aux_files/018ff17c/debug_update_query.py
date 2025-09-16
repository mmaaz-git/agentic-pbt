#!/usr/bin/env python3
"""Debug the update_query implementation issue."""

import sys
import urllib.parse
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

from google.auth import _helpers

url = 'http://example.com'
params = {'00': '', '0': '0'}

print("=== First call ===")
parts = urllib.parse.urlparse(url)
print(f"Original query: {parts.query}")

query_params = urllib.parse.parse_qs(parts.query)
print(f"Parsed query params: {query_params}")

query_params.update(params)
print(f"After update: {query_params}")

new_query = urllib.parse.urlencode(query_params, doseq=True)
print(f"Encoded query: {new_query}")

updated_url = _helpers.update_query(url, params)
print(f"Result URL: {updated_url}")

print("\n=== Second call ===")
parts2 = urllib.parse.urlparse(updated_url)
print(f"Query from first result: {parts2.query}")

query_params2 = urllib.parse.parse_qs(parts2.query)
print(f"Parsed query params: {query_params2}")

query_params2.update(params)
print(f"After update: {query_params2}")

new_query2 = urllib.parse.urlencode(query_params2, doseq=True)
print(f"Encoded query: {new_query2}")

updated_url2 = _helpers.update_query(updated_url, params)
print(f"Result URL: {updated_url2}")

print(f"\n=== Problem ===")
print(f"parse_qs returns lists: {urllib.parse.parse_qs('0=0&00=')}")
print(f"But update uses strings: {params}")
print(f"After dict.update(), mixed types: {{'0': ['0'], '00': ['']}} updated with {params} = ", end="")
test_dict = {'0': ['0'], '00': ['']}
test_dict.update(params)
print(test_dict)