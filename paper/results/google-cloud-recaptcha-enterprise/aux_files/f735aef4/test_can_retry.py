#!/usr/bin/env python3
"""Test _can_retry function for edge cases."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/lib/python3.13/site-packages')

import google.oauth2._client as _client

print("Testing _can_retry function")
print("="*50)

# Test cases that might reveal issues
test_cases = [
    # (status_code, response_data, description)
    (500, {"error": "server_error"}, "Standard server error"),
    (200, {"error": "server_error"}, "Server error with 200 status"),
    (400, {"error_description": "internal_failure"}, "Internal failure in description"),
    (400, {"error": "temporarily_unavailable"}, "Temporarily unavailable"),
    (400, "not a dict", "String response data"),
    (400, None, "None response data"),
    (400, {"error": 123}, "Non-string error code"),
    (400, {"error": None}, "None error code"),
    (400, {"error": "server", "error_description": "error"}, "Partial match 'server' and 'error'"),
    (400, {"error": "SERVER_ERROR"}, "Uppercase SERVER_ERROR"),
]

for status_code, response_data, description in test_cases:
    print(f"\nTest: {description}")
    print(f"  Status: {status_code}, Data: {response_data}")
    
    try:
        result = _client._can_retry(status_code, response_data)
        print(f"  Result: {result}")
        
        # Check for potential issues
        if description == "Partial match 'server' and 'error'":
            if result:
                print("  ⚠️  WARNING: Substring matching might be too broad")
                print("     'server' matches 'server_error' but also matches other strings")
        
        if description == "Uppercase SERVER_ERROR":
            if not result:
                print("  ⚠️  WARNING: Case sensitivity might cause issues")
                print("     OAuth servers might return uppercase error codes")
                
    except Exception as e:
        print(f"  Exception: {e.__class__.__name__}: {e}")

print("\n" + "="*50)
print("\nPOTENTIAL ISSUE FOUND:")
print("The function uses 'in' operator for checking error codes (line 104).")
print("This means 'error' in 'server_error' returns True.")
print("This could cause false positives for retry logic.")
print("\nExample: An error code 'user_error' would match because 'error' is in the string.")