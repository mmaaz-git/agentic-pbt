#!/usr/bin/env python3
"""Test edge cases for split_username to determine if behavior is a bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from spnego._context import split_username

# Test various edge cases
test_cases = [
    ("\\user", "Expected: ('\\', 'user') or error"),
    ("\\\\server\\share", "UNC path - Expected: ('\\\\server', 'share') or ('', '\\server\\share')"),
    ("DOMAIN\\", "Empty username - Expected: ('DOMAIN', '')"),
    ("\\", "Just backslash - Expected: ('', '') or error"),
    ("", "Empty string - Expected: (None, '')"),
    ("user", "No domain - Expected: (None, 'user')"),
    ("DOMAIN\\user\\extra", "Multiple backslashes - Expected: ('DOMAIN', 'user\\extra')"),
]

print("Testing split_username edge cases:")
print("=" * 60)

for input_str, description in test_cases:
    domain, user = split_username(input_str)
    print(f"Input: '{input_str}'")
    print(f"Description: {description}")
    print(f"Result: domain='{domain}', user='{user}'")
    print("-" * 60)

# Check what real Windows Netlogon format looks like
print("\nDocumentation check:")
print("The function claims to split 'Netlogon form `DOMAIN\\username`'")
print("In Windows Netlogon, a username starting with \\ typically means:")
print("1. Local machine reference (\\. or \\localhost)")
print("2. UNC path (\\\\server\\share)")
print("3. Malformed input")
print()
print("The current behavior treats '\\user' as having empty domain.")
print("This could be:")
print("1. A bug - domain should be '\\' or it should error")
print("2. Intended - empty domain means 'no domain specified'")
print()
print("Looking at line 44-46 of _context.py:")
print('    if "\\\\" in username:')
print('        domain, username = username.split("\\\\", 1)')
print("The code explicitly checks for backslash and splits on it.")
print("An empty domain from split() is not handled specially.")