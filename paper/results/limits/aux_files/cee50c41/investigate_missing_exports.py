#!/usr/bin/env python3
"""Investigate missing exports from __all__"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import limits.typing

print("Investigation: Missing exports in limits.typing.__all__")
print("=" * 60)

# Check what's in __all__
all_exports = set(limits.typing.__all__)
print(f"\nTotal items in __all__: {len(all_exports)}")

# Check public attributes
public_attrs = {name for name in dir(limits.typing) if not name.startswith('_')}
print(f"Total public attributes: {len(public_attrs)}")

# Find missing items
missing = public_attrs - all_exports
print(f"\nPublic attributes NOT in __all__: {missing}")

# Let's check each missing item
print("\nDetailed analysis of missing items:")
print("-" * 40)

for item in sorted(missing):
    if item == 'annotations':
        print(f"\n{item}: This is a special Python attribute, not a real export")
        continue
        
    attr = getattr(limits.typing, item)
    print(f"\n{item}:")
    print(f"  Type: {type(attr)}")
    print(f"  Value/Definition: {attr}")
    
    # Check if it's defined in the module
    if item in ['RedisClientP', 'AsyncRedisClientP', 'AsyncCoRedisClient']:
        # Look for it in the source
        with open('/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages/limits/typing.py', 'r') as f:
            source = f.read()
            
        # Check if it's defined
        if f'class {item}' in source:
            print(f"  ✓ Defined as a class in the module")
        elif f'{item}: TypeAlias' in source or f'{item} =' in source:
            print(f"  ✓ Defined as type alias in the module")
        else:
            print(f"  ? Definition pattern not found")
            
        # Check if it's used elsewhere
        import subprocess
        result = subprocess.run(
            ['grep', '-r', item, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages/limits/', 
             '--include=*.py'],
            capture_output=True, text=True
        )
        uses = [line for line in result.stdout.split('\n') if line and 'typing.py' not in line]
        if uses:
            print(f"  Used in {len(uses)} other file(s)")
            for use in uses[:3]:  # Show first 3 uses
                print(f"    - {use[:100]}...")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("-" * 60)

print("""
The following Protocol classes are defined in the module but NOT exported in __all__:
- RedisClientP (Protocol class, line 74)
- AsyncRedisClientP (Protocol class, line 84)
- AsyncCoRedisClient (Type alias, line 96)

However, the module DOES export:
- RedisClient (which is an alias for RedisClientP, line 94)
- AsyncRedisClient (which is an alias for AsyncRedisClientP, line 95)

This appears to be intentional design:
- The 'P' suffix versions are the actual Protocol classes
- The versions without 'P' are the public-facing type aliases
- AsyncCoRedisClient might be an oversight or intentionally internal

This could be:
1. Intentional: Only the aliases are meant to be public API
2. A bug: The Protocol classes should also be in __all__
3. Partial bug: AsyncCoRedisClient should be in __all__ but not the *P versions
""")