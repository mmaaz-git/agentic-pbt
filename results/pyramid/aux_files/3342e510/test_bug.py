#!/usr/bin/env python3
"""Demonstrate potential bug in pyramid.csrf is_same_domain function."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.util import is_same_domain

print("Testing is_same_domain for potential security bug...")
print("=" * 60)

# Bug: Pattern "." matches ANY non-empty domain
# This is likely unintended and could be a security issue

test_cases = [
    ("example.com", ".", True),  # Pattern "." matches any domain
    ("malicious.com", ".", True),  # Even malicious domains! 
    ("", ".", False),  # Empty string doesn't match
    ("a", ".", True),  # Single char matches
    (".", ".", True),  # Dot matches dot
]

print("\nDemonstrating bug: pattern '.' matches ANY non-empty domain")
print("This could be a security vulnerability if '.' is accidentally used as a pattern.\n")

bugs_found = []

for host, pattern, result in test_cases:
    actual = is_same_domain(host, pattern)
    status = "✓" if actual == result else "✗"
    print(f"{status} is_same_domain('{host}', '{pattern}') = {actual}")
    
    if pattern == "." and host and actual == True:
        bugs_found.append(f"Pattern '.' matched unrelated domain '{host}'")

if bugs_found:
    print("\n⚠️  SECURITY BUG FOUND:")
    print("Pattern '.' acts as a wildcard matching ANY non-empty domain!")
    print("This violates the principle of least privilege and could allow")
    print("unintended domains to pass CSRF origin checks.")
    print("\nAffected code (pyramid/util.py:633-636):")
    print("    return (")
    print("        pattern[0] == \".\"")
    print("        and (host.endswith(pattern) or host == pattern[1:])")
    print("        or pattern == host")
    print("    )")
    print("\nThe condition 'host.endswith(pattern)' with pattern='.' matches any")
    print("non-empty string since all strings 'end with' an empty string!")
    
    # Create reproduction script
    with open('reproduce_bug.py', 'w') as f:
        f.write('''#!/usr/bin/env python3
"""Minimal reproduction of is_same_domain bug with pattern '.'"."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
from pyramid.util import is_same_domain

# Bug: Pattern "." matches any non-empty domain
print("Testing is_same_domain with pattern '.':")
print(f"  is_same_domain('example.com', '.') = {is_same_domain('example.com', '.')}")
print(f"  is_same_domain('malicious.com', '.') = {is_same_domain('malicious.com', '.')}")
print(f"  is_same_domain('anything', '.') = {is_same_domain('anything', '.')}")

# This is because pattern[1:] when pattern="." gives empty string ""
# and host.endswith("") is always True for non-empty strings
print("\\nWhy this happens:")
print(f"  'example.com'.endswith('') = {'example.com'.endswith('')}")
print(f"  Pattern '.' -> pattern[1:] = {'.'[1:]!r}")
''')
    print("\n✅ Created 'reproduce_bug.py' for bug reproduction")
else:
    print("\nNo bugs found in this test.")

print("\n" + "=" * 60)