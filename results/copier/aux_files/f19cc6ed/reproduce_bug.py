#!/usr/bin/env python3
"""Minimal reproduction of the is_trusted prefix matching bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier.settings import Settings

# Test case 1: Prefix matching should work
settings = Settings(trust={'000000/'})
result = settings.is_trusted('000000')
print(f"Test 1: trust={{'000000/'}}, checking '000000'")
print(f"  Expected: True (prefix match)")
print(f"  Got: {result}")
print()

# Test case 2: Simpler case
settings2 = Settings(trust={'0/'})
result2 = settings2.is_trusted('00')
print(f"Test 2: trust={{'0/'}}, checking '00'")
print(f"  Expected: True (prefix match)")
print(f"  Got: {result2}")
print()

# Test case 3: Let's check what normalize does
settings3 = Settings(trust={'github.com/copier/'})
print(f"Test 3: trust={{'github.com/copier/'}}")
print(f"  Checking 'github.com/copier/template' -> {settings3.is_trusted('github.com/copier/template')}")
print(f"  Checking 'github.com/copier' -> {settings3.is_trusted('github.com/copier')}")
print()

# Let's look at the actual is_trusted implementation logic
print("Analyzing the is_trusted logic:")
settings4 = Settings(trust={'test/'})
test_repo = 'test'

print(f"Trust set: {settings4.trust}")
print(f"Testing repository: '{test_repo}'")

for trusted in settings4.trust:
    print(f"  Trusted pattern: '{trusted}'")
    if trusted.endswith("/"):
        print(f"    Pattern ends with '/', checking if '{test_repo}'.startswith('{trusted}')")
        print(f"    Result: {test_repo.startswith(trusted)}")
        # This is the issue! 'test' does not start with 'test/'
        # The code checks if repository starts with the full trusted string including the slash
        # But it should check if it starts with the prefix without the slash
        
        # What it should check:
        prefix = trusted[:-1]  # Remove the trailing slash
        print(f"    Should check: '{test_repo}'.startswith('{prefix}')")
        print(f"    That would give: {test_repo.startswith(prefix)}")