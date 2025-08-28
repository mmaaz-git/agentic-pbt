"""Minimal reproductions of discovered bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.authentication import (
    AuthTicket, parse_ticket,
    encode_ip_timestamp, calculate_digest,
    VALID_TOKEN
)

print("Bug 1: Invalid IP address handling in encode_ip_timestamp")
print("=" * 60)
try:
    # IP with octet > 255
    result = encode_ip_timestamp('0.0.0.260', 0)
    print(f"ERROR: Should have failed but returned: {result}")
except Exception as e:
    print(f"Exception raised: {type(e).__name__}: {e}")
    print("This should be caught and handled gracefully, not crash with UnicodeEncodeError")

print("\n" + "=" * 60)
print("Bug 2: Empty tokens list parsed incorrectly")
print("=" * 60)

# Create ticket with empty tokens list
ticket = AuthTicket(
    secret='secret',
    userid='testuser',
    ip='127.0.0.1',
    tokens=[],  # Empty list
    user_data='',
    hashalg='md5'
)

cookie_value = ticket.cookie_value()
print(f"Cookie value with empty tokens: {cookie_value}")

# Parse it back
timestamp, userid, tokens, user_data = parse_ticket(
    secret='secret',
    ticket=cookie_value,
    ip='127.0.0.1',
    hashalg='md5'
)

print(f"Original tokens: []")
print(f"Parsed tokens:   {tokens}")
print(f"Are they equal? {[] == tokens}")
print(f"Bug: Empty list becomes [''] instead of []")

print("\n" + "=" * 60)
print("Bug 3: VALID_TOKEN regex accepts Unicode letters")
print("=" * 60)

# Test with Unicode letter
unicode_token = 'À'
match = VALID_TOKEN.match(unicode_token)
print(f"Token: '{unicode_token}'")
print(f"VALID_TOKEN.match('{unicode_token}'): {match}")
print(f"Pattern claims: ^[A-Za-z][A-Za-z0-9+_-]*$")
print(f"Bug: Pattern should only accept ASCII letters, but accepts Unicode")

# Test that it's supposed to be ASCII only
print("\nEvidence this is a bug:")
print("Line 1178-1179 in authentication.py validates tokens with:")
print("  if not (isinstance(token, str) and VALID_TOKEN.match(token)):")
print("      raise ValueError('Invalid token %r' % (token,))")
print("\nBut line 1175 first converts to ASCII:")
print("  token = ascii_(token)")
print("This shows tokens are meant to be ASCII-only")