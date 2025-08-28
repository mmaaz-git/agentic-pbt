#!/usr/bin/env python3
"""Discover a potential bug in OAuth2Session PKCE validation."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

# Looking at the PKCE validation code (lines 89-90):
# if self._pkce not in ["S256", "plain", None]:
#     raise AttributeError("Wrong value for {}(.., pkce={})".format(self.__class__, self._pkce))

# The validation happens AFTER setting self._pkce = pkce on line 87
# This means if we look carefully at the error message, it will contain the invalid value

# Let me trace through what happens with different edge cases:

print("=== Analyzing PKCE Validation Logic ===\n")

# The check is: if self._pkce not in ["S256", "plain", None]
# This uses Python's 'in' operator which checks for equality

# Edge case 1: What about boolean False?
# False == 0 in Python, and 0 != any of ["S256", "plain", None]
# So False should be rejected

# Edge case 2: What about boolean True?  
# True == 1 in Python, and 1 != any of ["S256", "plain", None]
# So True should be rejected

# Edge case 3: What about empty string ""?
# "" != any of ["S256", "plain", None] 
# So "" should be rejected

# Edge case 4: What about integer 0?
# 0 != any of ["S256", "plain", None]
# So 0 should be rejected

# Actually, wait - I realize the formatting issue in the error message could be a bug!
# Look at line 90:
# raise AttributeError("Wrong value for {}(.., pkce={})".format(self.__class__, self._pkce))

# The issue is that self.__class__ will produce something like:
# <class 'requests_oauthlib.oauth2_session.OAuth2Session'>
# This makes the error message look like:
# "Wrong value for <class 'requests_oauthlib.oauth2_session.OAuth2Session'>(.., pkce=invalid)"

# This is poor UX - it should probably be self.__class__.__name__ to get just "OAuth2Session"

print("Potential Bug Found: Error message formatting issue")
print("="*50)
print("\nThe error message on line 90 uses:")
print("  'Wrong value for {}(.., pkce={})'.format(self.__class__, self._pkce)")
print("\nThis will produce messages like:")
print("  'Wrong value for <class 'requests_oauthlib.oauth2_session.OAuth2Session'>(.., pkce=invalid)'")
print("\nIt should probably use self.__class__.__name__ instead to produce:")
print("  'Wrong value for OAuth2Session(.., pkce=invalid)'")
print("\nThis is a minor UX bug but still a legitimate issue.")

# Let me also check for any logical bugs in the validation itself
print("\n" + "="*50)
print("\nAnalyzing the validation logic more deeply...")

# Actually, I notice another potential issue!
# The validation on line 89 checks:
#   if self._pkce not in ["S256", "plain", None]:

# But what if someone passes pkce=0 or pkce=False?
# In Python, False == 0, but neither equals None
# So these would be correctly rejected

# However, there's a subtlety: The 'in' operator uses equality (==) not identity (is)
# This means that if someone creates a custom object that implements __eq__ to equal "S256",
# it would pass validation even though it's not actually the string "S256"

# This could potentially be a security issue if someone can control the pkce parameter
# with a malicious object that claims to equal "S256" but behaves differently

print("\nAnother potential issue found:")
print("The validation uses 'in' which relies on == equality rather than identity.")
print("This means custom objects with overridden __eq__ could bypass validation.")
print("While unlikely to be exploitable in practice, it's technically a logical flaw.")

# Let me check one more thing - what about case sensitivity?
print("\n" + "="*50)
print("\nChecking case sensitivity...")
print("The valid values are 'S256' and 'plain' (case-sensitive)")
print("So 's256', 'Plain', 'PLAIN' etc. would all be rejected")
print("This is correct per the PKCE spec (RFC 7636) which specifies exact values")

print("\n=== Summary ===")
print("1. UX Bug: Error message formatting uses self.__class__ instead of self.__class__.__name__")
print("2. Minor logical issue: Uses == equality instead of identity for validation")
print("3. The validation itself appears correct for standard inputs")