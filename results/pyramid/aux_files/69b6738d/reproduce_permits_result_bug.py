"""Minimal reproduction of PermitsResult.msg formatting bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.security import Denied, Allowed

print("Testing PermitsResult.msg property with malformed format strings...")
print("=" * 60)

# Test 1: Invalid format specifier
print("\n1. Invalid format specifier '%A':")
try:
    denied = Denied('%A')
    msg = denied.msg
    print(f"   Result: {msg}")
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")

# Test 2: Incomplete format string
print("\n2. Incomplete format string '%':")
try:
    denied = Denied('%')
    msg = denied.msg
    print(f"   Result: {msg}")
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")

# Test 3: Too many format specifiers
print("\n3. Too many format specifiers '%s %s' with one arg:")
try:
    allowed = Allowed('%s %s', 'arg1')
    msg = allowed.msg
    print(f"   Result: {msg}")
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")

# Test 4: Format string with wrong type specifier
print("\n4. Format string '%d' with string arg:")
try:
    denied = Denied('%d', 'not_a_number')
    msg = denied.msg
    print(f"   Result: {msg}")
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("SUMMARY: PermitsResult.msg crashes on malformed format strings")
print("This affects both Denied and Allowed classes which are public API")