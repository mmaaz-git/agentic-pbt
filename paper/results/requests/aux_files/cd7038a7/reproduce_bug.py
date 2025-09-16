#!/usr/bin/env python3
"""Minimal reproduction of Unicode encoding bug in requests.auth._basic_auth_str"""

import requests.auth

# Test case 1: Unicode character in username
try:
    result = requests.auth._basic_auth_str('Ā', 'password')
    print(f"Success with unicode username: {result}")
except UnicodeEncodeError as e:
    print(f"BUG: UnicodeEncodeError with unicode username 'Ā': {e}")

# Test case 2: Unicode character in password  
try:
    result = requests.auth._basic_auth_str('username', 'Ā')
    print(f"Success with unicode password: {result}")
except UnicodeEncodeError as e:
    print(f"BUG: UnicodeEncodeError with unicode password 'Ā': {e}")

# Test case 3: Common international characters
test_strings = ['café', 'naïve', '北京', 'Москва', 'مرحبا']
for test_str in test_strings:
    try:
        result = requests.auth._basic_auth_str(test_str, 'password')
        print(f"Success with '{test_str}': {result[:20]}...")
    except UnicodeEncodeError as e:
        print(f"BUG: Failed with '{test_str}': {e}")

# Demonstrate the issue with HTTPBasicAuth
print("\n--- Testing with HTTPBasicAuth class ---")
try:
    auth = requests.auth.HTTPBasicAuth('user_Ā', 'pass')
    # Create mock request
    class MockRequest:
        def __init__(self):
            self.headers = {}
    
    r = MockRequest()
    auth(r)  # This will call _basic_auth_str internally
    print(f"Success: {r.headers}")
except UnicodeEncodeError as e:
    print(f"BUG in HTTPBasicAuth: {e}")