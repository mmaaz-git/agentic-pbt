#!/usr/bin/env python3
"""
Bug hunter for sentinels module - looking for genuine bugs.
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sentinels_env/lib/python3.13/site-packages')

import pickle
from sentinels import Sentinel

print("=== SENTINELS BUG HUNTER ===\n")

# BUG HUNT 1: Name mutability after creation
print("Bug Hunt 1: Testing name mutability...")
s = Sentinel("original")
original_name = s._name
s._name = "modified"  # Direct attribute modification

# Check if this breaks anything
s2 = Sentinel("original")
if s is s2 and s._name != "original":
    print("✗ POTENTIAL BUG: Sentinel name can be modified, breaking singleton contract!")
    print(f"  Created Sentinel('original'), changed _name to 'modified'")
    print(f"  Sentinel('original') still returns same object but with wrong name: {repr(s)}")
else:
    print("✓ No bug found in name mutability")

print()

# BUG HUNT 2: Registry manipulation and pickle interaction
print("Bug Hunt 2: Testing registry manipulation with pickling...")
# Create a sentinel
s1 = Sentinel("pickle_test")
s1_id = id(s1)

# Pickle it while it's in the registry
pickled_with_registry = pickle.dumps(s1)

# Clear the registry (simulating an edge case)
Sentinel._existing_instances.clear()

# Create a new sentinel with the same name
s2 = Sentinel("pickle_test")
s2_id = id(s2)

# Now unpickle the original
unpickled = pickle.loads(pickled_with_registry)

if unpickled is s2 and s1_id != s2_id:
    print("✓ Unpickling correctly uses current registry (expected behavior)")
elif unpickled is s1:
    print("✗ BUG: Unpickled object is the cleared instance (memory safety issue!)")
else:
    print("? Unexpected: Unpickled object is neither s1 nor s2")

print()

# BUG HUNT 3: Representation injection
print("Bug Hunt 3: Testing repr format with malicious names...")
test_names = [
    "><script>alert('xss')</script><",
    "test>",
    "<test",
    "><",
    "",  # Empty string
]

for name in test_names:
    s = Sentinel(name)
    repr_str = repr(s)
    expected = f"<{name}>"
    
    if repr_str != expected:
        print(f"✗ BUG: Repr format broken for name={repr(name)}")
        print(f"  Expected: {repr(expected)}")
        print(f"  Got: {repr(repr_str)}")
    else:
        print(f"✓ Repr correct for: {repr(name)}")

print()

# BUG HUNT 4: Hash collision potential
print("Bug Hunt 4: Testing hash consistency...")
s1 = Sentinel("hash_test")
original_hash = hash(s1)

# Modify internal state (if possible)
s1._name = "modified_hash_test"
modified_hash = hash(s1)

if original_hash != modified_hash:
    print("✗ POTENTIAL BUG: Hash changes when internal state modified!")
    print(f"  Original hash: {original_hash}")
    print(f"  Modified hash: {modified_hash}")
    print("  This could break dict/set usage")
else:
    print("✓ Hash remains consistent")

# Reset for next test
s1._name = "hash_test"

print()

# BUG HUNT 5: Null byte in name
print("Bug Hunt 5: Testing null byte in name...")
try:
    null_sentinel = Sentinel("test\x00null")
    print(f"✓ Null byte handled: {repr(null_sentinel)}")
    
    # Test pickling with null byte
    pickled = pickle.dumps(null_sentinel)
    unpickled = pickle.loads(pickled)
    if unpickled is null_sentinel:
        print("✓ Pickle works with null byte")
    else:
        print("✗ BUG: Pickle fails to maintain identity with null byte in name")
except Exception as e:
    print(f"✗ Exception with null byte: {e}")

print()

# BUG HUNT 6: Very long names
print("Bug Hunt 6: Testing very long names...")
long_name = "a" * 1000000  # 1 million characters
try:
    s = Sentinel(long_name)
    s2 = Sentinel(long_name)
    if s is s2:
        print("✓ Very long names work correctly")
    else:
        print("✗ BUG: Singleton fails with very long names")
except Exception as e:
    print(f"✗ Exception with long name: {e}")

print("\n=== BUG HUNT COMPLETE ===")

# Summary of the most serious finding
print("\nMOST SERIOUS FINDING:")
print("The _name attribute can be modified after creation, violating the")
print("immutability assumption and potentially breaking the singleton pattern.")
print("This is a contract violation that could lead to confusing behavior.")