#!/usr/bin/env python3
"""Manually test OAuth2Session properties to find bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import WebApplicationClient

print("=== Manual Property Testing ===\n")

# Test 1: PKCE validation with empty string
print("Test 1: PKCE validation with empty string...")
try:
    session = OAuth2Session(client_id="test", pkce="")
    print("BUG FOUND: Empty string accepted as PKCE value!")
    print(f"Session created with pkce='', _pkce={session._pkce}")
except AttributeError as e:
    print(f"Correctly rejected empty PKCE: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

# Test 2: PKCE validation with numeric value
print("\nTest 2: PKCE validation with numeric value...")
try:
    session = OAuth2Session(client_id="test", pkce="256")
    print("BUG FOUND: '256' accepted as PKCE value!")
    print(f"Session created with pkce='256', _pkce={session._pkce}")
except AttributeError as e:
    print(f"Correctly rejected '256': {e}")
except Exception as e:
    print(f"Unexpected error: {e}")

# Test 3: Token property with empty dict
print("\nTest 3: Token property with empty dict...")
session = OAuth2Session(client_id="test")
session.token = {}
print(f"Set token to empty dict: session.token = {session.token}")
print(f"Client token: session._client.token = {session._client.token}")
if session.token != {} or session._client.token != {}:
    print("BUG: Token not properly synchronized!")

# Test 4: Scope fallback with None values
print("\nTest 4: Scope property fallback...")
client = WebApplicationClient("test")
client.scope = ["read", "write"]
session = OAuth2Session(client=client, scope=None)
print(f"Client scope: {client.scope}")
print(f"Session scope (None): {session._scope}")
print(f"session.scope property: {session.scope}")
if session.scope != ["read", "write"]:
    print("BUG: Scope should fallback to client scope!")

# Test 5: Invalid hook type with special characters
print("\nTest 5: Invalid hook type registration...")
session = OAuth2Session()
try:
    session.register_compliance_hook("!@#$%", lambda: None)
    print("BUG FOUND: Invalid hook type '!@#$%' was accepted!")
except ValueError as e:
    print(f"Correctly rejected invalid hook: {e}")

# Test 6: Check if hooks are really sets
print("\nTest 6: Hook uniqueness (set behavior)...")
session = OAuth2Session()
def my_hook():
    pass

session.register_compliance_hook("protected_request", my_hook)
session.register_compliance_hook("protected_request", my_hook)
session.register_compliance_hook("protected_request", my_hook)

hook_count = len(session.compliance_hook["protected_request"])
print(f"Registered same hook 3 times, count in set: {hook_count}")
if hook_count != 1:
    print(f"BUG: Expected 1 hook in set, got {hook_count}")

# Test 7: Client ID deletion
print("\nTest 7: Client ID deletion...")
session = OAuth2Session(client_id="test123")
print(f"Initial client_id: {session.client_id}")
del session.client_id
print(f"After deletion: {session.client_id}")
if session.client_id is not None:
    print(f"BUG: client_id should be None after deletion, got {session.client_id}")

# Test 8: State generation with None
print("\nTest 8: State generation...")
session = OAuth2Session(client_id="test", state=None)
print(f"Initial state: {session.state}")
print(f"Initial _state: {session._state}")
new_state = session.new_state()
print(f"Generated state: {new_state}")
print(f"Type of state generator: {type(session.state)}")

# Test 9: Authorization URL with empty string state
print("\nTest 9: Authorization URL generation...")
session = OAuth2Session(client_id="test", state="")
url, state = session.authorization_url("https://example.com/authorize")
print(f"State used: '{state}'")
print(f"URL generated: {url[:50]}...")

# Test 10: Access token with None
print("\nTest 10: Access token with None...")
session = OAuth2Session(client_id="test")
session.access_token = None
print(f"Set access_token to None: {session.access_token}")
print(f"Authorized property: {session.authorized}")
if session.authorized:
    print("BUG: authorized should be False when access_token is None")

print("\n=== Testing Complete ===")