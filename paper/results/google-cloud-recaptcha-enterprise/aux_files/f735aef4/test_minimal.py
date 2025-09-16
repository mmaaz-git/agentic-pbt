#!/usr/bin/env python3
"""Minimal reproducible test cases for potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

import google.oauth2._client as _client

# BUG CANDIDATE: Expiry parsing with float strings
print("Testing potential bug in _parse_expiry:")
print("="*50)

# This should raise an error but might not
response = {"expires_in": "3600.5"}
print(f"Input: {response}")

try:
    expiry = _client._parse_expiry(response)
    print(f"Result: {expiry}")
    print("STATUS: Potential bug - float string accepted without proper handling")
    print("\nThe code at _client.py line 129 does:")
    print('  expires_in = int(expires_in)')
    print("\nThis will raise ValueError for '3600.5' but the error isn't caught.")
    print("This could cause unexpected failures when OAuth servers return float strings.")
except ValueError as e:
    print(f"ValueError raised: {e}")
    print("STATUS: Expected behavior - ValueError for invalid string format")

print("\n" + "="*50)
print("\nTo reproduce:")
print("1. Call _parse_expiry with {'expires_in': '3600.5'}")
print("2. Observe ValueError is raised")
print("3. This could break token refresh if server returns float expires_in")