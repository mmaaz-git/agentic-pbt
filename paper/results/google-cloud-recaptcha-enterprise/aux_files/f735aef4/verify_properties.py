#!/usr/bin/env python3
"""Verify specific properties with potentially problematic inputs."""

import sys
import json
import base64
import urllib.parse
import datetime

sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

import google.oauth2.utils as utils
import google.oauth2._client as _client

print("VERIFYING GOOGLE.OAUTH2 PROPERTIES")
print("="*60)

# Finding 1: Test expiry parsing with float strings
print("\nFINDING 1: Expiry parsing with float string")
print("-"*40)
print("Code location: google/oauth2/_client.py lines 123-133")
print("The code converts string expires_in to int, but what about float strings?")

test_cases = [
    "3600",      # Normal case
    "3600.0",    # Float string  
    "3600.5",    # Float with decimal
    "1e3",       # Scientific notation
]

for test_value in test_cases:
    print(f"\nTesting expires_in = '{test_value}'")
    response = {"expires_in": test_value}
    try:
        expiry = _client._parse_expiry(response)
        print(f"  ✓ Parsed successfully: {expiry}")
    except ValueError as e:
        print(f"  ✗ ValueError: {e}")
    except Exception as e:
        print(f"  ✗ {e.__class__.__name__}: {e}")

# Finding 2: Test error handling with edge cases
print("\n\nFINDING 2: Error response handling edge cases")
print("-"*40)
print("Code location: google/oauth2/utils.py lines 144-168")

edge_cases = [
    ('{"error": "test"}', "Valid JSON with error"),
    ('{"error": "test", "error_description": null}', "JSON with null description"),
    ('{"error": 123}', "Non-string error code"),
    ('{"error": true}', "Boolean error code"),
    ('{"error": ["array"]}', "Array as error code"),
]

for response_body, description in edge_cases:
    print(f"\nTesting: {description}")
    print(f"Input: {response_body}")
    try:
        utils.handle_error_response(response_body)
        print("  ✗ No exception raised!")
    except Exception as e:
        print(f"  Exception: {e.__class__.__name__}")
        error_msg = str(e)
        if "Error code" in error_msg:
            print(f"  Message contains 'Error code': Yes")
        else:
            print(f"  Message: {error_msg[:100]}")

# Finding 3: Base64 encoding with special characters
print("\n\nFINDING 3: Base64 encoding with special characters")
print("-"*40)
print("Code location: google/oauth2/utils.py lines 122-124")

special_cases = [
    ("user", "pass"),              # Normal
    ("user:name", "pass:word"),    # Colons in credentials
    ("user", ""),                  # Empty password
    ("", "password"),              # Empty username
    ("user\nname", "pass\nword"),  # Newlines
    ("user\x00name", "pass"),      # Null bytes
]

for client_id, client_secret in special_cases:
    print(f"\nTesting client_id='{repr(client_id)}', client_secret='{repr(client_secret)}'")
    try:
        client_auth = utils.ClientAuthentication(
            utils.ClientAuthType.basic,
            client_id,
            client_secret
        )
        handler = utils.OAuthClientAuthHandler(client_auth)
        headers = {}
        handler.apply_client_authentication_options(headers)
        
        if "Authorization" in headers:
            auth_header = headers["Authorization"]
            b64_part = auth_header[6:]  # Remove "Basic "
            decoded = base64.b64decode(b64_part).decode('utf-8')
            expected = f"{client_id}:{client_secret if client_secret else ''}"
            
            if decoded == expected:
                print(f"  ✓ Round-trip successful")
            else:
                print(f"  ✗ Mismatch!")
                print(f"    Expected: {repr(expected)}")
                print(f"    Got: {repr(decoded)}")
    except Exception as e:
        print(f"  ✗ Exception: {e.__class__.__name__}: {e}")

print("\n" + "="*60)
print("VERIFICATION COMPLETE")
print("Check the results above for any unexpected behavior or failures.")