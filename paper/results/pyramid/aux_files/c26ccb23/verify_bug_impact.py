"""Verify the impact and legitimacy of discovered bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.authentication import AuthTicket, parse_ticket, encode_ip_timestamp

print("Bug 1 Impact: Invalid IP addresses crash encode_ip_timestamp")
print("=" * 70)
print("The function encode_ip_timestamp is used internally by:")
print("- calculate_digest (line 799)")
print("- AuthTicket.digest() -> calculate_digest")
print("- AuthTicket.cookie_value() -> digest()")
print()
print("Real-world impact:")
print("- If user input or misconfigured system provides IP like '192.168.1.300'")
print("- The entire authentication system crashes with UnicodeEncodeError")
print("- This is a crash bug that could cause service disruption")
print()
print("Expected behavior: Should validate IP octets are 0-255")
print()

print("Bug 2 Impact: Empty tokens list incorrectly round-trips")
print("=" * 70)
print("Documentation at line 667-680 shows AuthTicket usage:")
print("  token = AuthTicket('sharedsecret', 'username',")
print("      os.environ['REMOTE_ADDR'], tokens=['admin'])")
print()
print("The tokens parameter (line 688) accepts a tuple/list.")
print("When tokens=[], the ticket stores no tokens.")
print("But when parsed back, it returns [''] instead of [].")
print()
print("Real-world impact:")
print("- Applications checking 'if tokens:' will get different behavior")
print("- Empty list (falsy) becomes [''] (truthy)")
print("- This breaks the round-trip property and can cause logic bugs")
print()

# Demonstrate the actual issue
print("Demonstration:")
ticket1 = AuthTicket('secret', 'user', '127.0.0.1', tokens=[], hashalg='md5')
cookie = ticket1.cookie_value()
_, _, parsed_tokens, _ = parse_ticket('secret', cookie, '127.0.0.1', 'md5')

print(f"  Original: tokens={[]}")
print(f"  Parsed:   tokens={parsed_tokens}")
print(f"  bool([]): {bool([])}")
print(f"  bool({parsed_tokens}): {bool(parsed_tokens)}")
print()
print("This violates the expected round-trip property of serialization.")