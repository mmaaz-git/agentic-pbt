#!/usr/bin/env python3
"""Reproduce the bug where CookieCSRFStoragePolicy modifies request.cookies."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.csrf import CookieCSRFStoragePolicy
from unittest.mock import Mock

print("Reproducing CookieCSRFStoragePolicy bug...")
print("=" * 60)

# Create a mock request
request = Mock()
request.cookies = {}  # Client sent no cookies
request.add_response_callback = Mock()

print("Initial state:")
print(f"  request.cookies = {request.cookies}")

# Create policy and generate new token
policy = CookieCSRFStoragePolicy(cookie_name='csrf_token')
token = policy.new_csrf_token(request)

print(f"\nAfter calling new_csrf_token():")
print(f"  Generated token: {token}")
print(f"  request.cookies = {request.cookies}")

# The bug: request.cookies now contains the token!
if 'csrf_token' in request.cookies:
    print("\n❌ BUG CONFIRMED!")
    print("  request.cookies was modified to include the new token.")
    print("  This makes it appear as if the client sent this token,")
    print("  when in reality it was just generated server-side.")
    
    # Demonstrate the confusion this causes
    print("\nDemonstrating the problem:")
    print("  Another part of the code checks if client sent a token:")
    if request.cookies.get('csrf_token'):
        print("  ✗ Code thinks: 'Client sent CSRF token'")
        print("  ✗ Reality: Token was generated server-side!")
    
    print("\nThis violates the principle that request data should be immutable.")
    print("Request objects should represent what the client sent, not be modified.")
else:
    print("\n✓ No bug - request.cookies was not modified")

print("\n" + "=" * 60)