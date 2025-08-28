#!/usr/bin/env python3
"""Test expiry parsing in google.oauth2._client."""

import sys
import datetime

sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

import google.oauth2._client as _client

print("Testing expiry parsing...")

# Test with integer
print("\n1. Testing with integer expires_in:")
response1 = {"expires_in": 3600}
expiry1 = _client._parse_expiry(response1)
print(f"Input: {response1}")
print(f"Result type: {type(expiry1)}")
print(f"Result: {expiry1}")

# Test with string
print("\n2. Testing with string expires_in:")
response2 = {"expires_in": "7200"}
expiry2 = _client._parse_expiry(response2)
print(f"Input: {response2}")
print(f"Result type: {type(expiry2)}")
print(f"Result: {expiry2}")

# Test with None
print("\n3. Testing with no expires_in:")
response3 = {}
expiry3 = _client._parse_expiry(response3)
print(f"Input: {response3}")
print(f"Result: {expiry3}")

# Test with invalid string (should this work?)
print("\n4. Testing with non-numeric string:")
response4 = {"expires_in": "invalid"}
try:
    expiry4 = _client._parse_expiry(response4)
    print(f"Input: {response4}")
    print(f"Result: {expiry4}")
except Exception as e:
    print(f"Input: {response4}")
    print(f"Exception: {e.__class__.__name__}: {e}")

# Test with negative value
print("\n5. Testing with negative expires_in:")
response5 = {"expires_in": -100}
expiry5 = _client._parse_expiry(response5)
now = datetime.datetime.utcnow()
print(f"Input: {response5}")
print(f"Result: {expiry5}")
print(f"Current time: {now}")
print(f"Is expiry in past? {expiry5 < now if expiry5 else 'N/A'}")

# Test with float string
print("\n6. Testing with float string expires_in:")
response6 = {"expires_in": "3600.5"}
try:
    expiry6 = _client._parse_expiry(response6)
    print(f"Input: {response6}")
    print(f"Result: {expiry6}")
except Exception as e:
    print(f"Input: {response6}")
    print(f"Exception: {e.__class__.__name__}: {e}")