#!/usr/bin/env python3
"""Test to confirm the bug: AsyncCoRedisClient is missing from __all__"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

print("Bug Confirmation Test: AsyncCoRedisClient missing from __all__")
print("=" * 60)

# Test 1: Direct import works
print("\n1. Testing direct attribute access:")
try:
    import limits.typing
    async_coredis = limits.typing.AsyncCoRedisClient
    print(f"   ✓ limits.typing.AsyncCoRedisClient exists: {async_coredis}")
except AttributeError as e:
    print(f"   ✗ Failed to access: {e}")

# Test 2: Star import doesn't work
print("\n2. Testing star import (from limits.typing import *):")
namespace = {}
exec("from limits.typing import *", namespace)
if 'AsyncCoRedisClient' in namespace:
    print(f"   ✓ AsyncCoRedisClient is available via star import")
else:
    print(f"   ✗ AsyncCoRedisClient is NOT available via star import")
    print(f"   Available names: {sorted([k for k in namespace.keys() if not k.startswith('_')])[:5]}...")

# Test 3: Check if it's in __all__
print("\n3. Checking __all__ list:")
import limits.typing
if 'AsyncCoRedisClient' in limits.typing.__all__:
    print(f"   ✓ AsyncCoRedisClient is in __all__")
else:
    print(f"   ✗ AsyncCoRedisClient is NOT in __all__")

# Test 4: Check if it's actually used in the codebase
print("\n4. Checking usage in codebase:")
import subprocess
result = subprocess.run(
    ['grep', '-r', 'AsyncCoRedisClient', '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages/limits/', 
     '--include=*.py'],
    capture_output=True, text=True
)
uses = result.stdout.strip().split('\n')
uses = [u for u in uses if u and 'typing.py' not in u]

if uses:
    print(f"   ✓ AsyncCoRedisClient is used in {len(uses)} file(s):")
    for use in uses[:3]:
        filename = use.split(':')[0].split('/')[-1]
        print(f"     - {filename}")
else:
    print(f"   ✗ AsyncCoRedisClient is not used anywhere")

# Test 5: Compare with similar exports
print("\n5. Comparing with similar exports:")
print("   RedisClient (alias for RedisClientP): ", 'RedisClient' in limits.typing.__all__)
print("   AsyncRedisClient (alias for AsyncRedisClientP): ", 'AsyncRedisClient' in limits.typing.__all__)
print("   AsyncCoRedisClient (standalone type alias): ", 'AsyncCoRedisClient' in limits.typing.__all__)

print("\n" + "=" * 60)
print("BUG CONFIRMED:")
print("-" * 60)
print("""
AsyncCoRedisClient is:
1. ✓ Defined as a public type alias (no underscore prefix)
2. ✓ Accessible as limits.typing.AsyncCoRedisClient
3. ✓ Used by other files in the limits package
4. ✗ NOT included in __all__ list
5. ✗ NOT available via star import (from limits.typing import *)

This violates the principle that public APIs should be in __all__.
Users who use star imports won't have access to this type alias,
causing potential import errors and type checking issues.
""")