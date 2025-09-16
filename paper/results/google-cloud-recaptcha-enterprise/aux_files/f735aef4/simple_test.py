#!/usr/bin/env python3
"""Simple property test for google.oauth2."""

import sys
import json
import base64
import urllib.parse

sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

import google.oauth2.utils as utils

# Test 1: Base64 encoding with special characters
print("Test 1: Base64 encoding with special characters")
client_id = "user@example.com"
client_secret = "p@ssw0rd!#$%"

client_auth = utils.ClientAuthentication(
    utils.ClientAuthType.basic,
    client_id,
    client_secret
)

handler = utils.OAuthClientAuthHandler(client_auth)
headers = {}
handler.apply_client_authentication_options(headers)

auth_header = headers.get("Authorization", "")
print(f"Auth header: {auth_header}")

if auth_header.startswith("Basic "):
    b64_part = auth_header[6:]
    decoded = base64.b64decode(b64_part).decode('utf-8')
    expected = f"{client_id}:{client_secret}"
    print(f"Decoded: {decoded}")
    print(f"Expected: {expected}")
    print(f"Match: {decoded == expected}")

# Test 2: Error response with malformed JSON
print("\nTest 2: Error response handling")
malformed_json = '{"error": "invalid_grant", "error_description": "Token has been expired or revoked."'
print(f"Testing with malformed JSON: {malformed_json}")

try:
    utils.handle_error_response(malformed_json)
except Exception as e:
    print(f"Exception raised: {e.__class__.__name__}")
    print(f"Error message: {e}")

# Test 3: Error response with unicode characters
print("\nTest 3: Error response with unicode")
unicode_error = json.dumps({"error": "invalid_request", "error_description": "Invalid character: 你好世界 🚀"})
print(f"Testing with unicode: {unicode_error}")

try:
    utils.handle_error_response(unicode_error)
except Exception as e:
    print(f"Exception raised: {e.__class__.__name__}")
    print(f"Error message: {e}")