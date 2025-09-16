#!/usr/bin/env python3
"""Simple test to find a specific bug in OAuth2Session."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib import OAuth2Session

# Looking at line 89-90 of oauth2_session.py:
# if self._pkce not in ["S256", "plain", None]:
#     raise AttributeError("Wrong value for {}(.., pkce={})".format(self.__class__, self._pkce))

# Bug hypothesis: Empty string "" should be invalid but might not be caught

print("Testing PKCE validation with empty string...")

# Test case 1: Empty string
try:
    session = OAuth2Session(client_id="test", pkce="")
    # If we get here, there's a bug - empty string shouldn't be valid
    print(f"BUG FOUND: Empty string '' was accepted as valid PKCE value!")
    print(f"Session._pkce = {repr(session._pkce)}")
    print("\nThis violates the PKCE specification which only allows 'S256', 'plain', or None")
except AttributeError as e:
    print(f"Good: Empty string correctly rejected with: {e}")

# Test case 2: Boolean False (edge case)
try:
    session = OAuth2Session(client_id="test", pkce=False)
    print(f"Potential issue: Boolean False accepted, _pkce = {repr(session._pkce)}")
except AttributeError as e:
    print(f"Good: Boolean False rejected with: {e}")

# Test case 3: Boolean True (edge case)  
try:
    session = OAuth2Session(client_id="test", pkce=True)
    print(f"Potential issue: Boolean True accepted, _pkce = {repr(session._pkce)}")
except AttributeError as e:
    print(f"Good: Boolean True rejected with: {e}")

# Test case 4: Integer 0 (edge case)
try:
    session = OAuth2Session(client_id="test", pkce=0)
    print(f"Potential issue: Integer 0 accepted, _pkce = {repr(session._pkce)}")
except AttributeError as e:
    print(f"Good: Integer 0 rejected with: {e}")