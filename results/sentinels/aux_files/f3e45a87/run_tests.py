#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sentinels_env/lib/python3.13/site-packages')

import pickle
from sentinels import Sentinel

# Test 1: Singleton property
print("Testing singleton property...")
try:
    sentinel1 = Sentinel("test")
    sentinel2 = Sentinel("test")
    assert sentinel1 is sentinel2
    print("✓ Singleton property works for 'test'")
except AssertionError as e:
    print(f"✗ Singleton property failed: {e}")

# Test 2: Pickle round-trip
print("\nTesting pickle round-trip...")
try:
    original = Sentinel("pickle_test")
    pickled = pickle.dumps(original)
    unpickled = pickle.loads(pickled)
    assert unpickled is original
    print("✓ Pickle round-trip maintains identity")
except AssertionError as e:
    print(f"✗ Pickle round-trip failed: {e}")

# Test 3: Repr format
print("\nTesting repr format...")
try:
    sentinel = Sentinel("repr_test")
    expected = "<repr_test>"
    assert repr(sentinel) == expected
    print(f"✓ Repr format correct: {repr(sentinel)}")
except AssertionError as e:
    print(f"✗ Repr format failed: {e}")

# Test 4: Empty string name
print("\nTesting edge case: empty string name...")
try:
    empty_sentinel = Sentinel("")
    assert repr(empty_sentinel) == "<>"
    print(f"✓ Empty string name works: {repr(empty_sentinel)}")
except Exception as e:
    print(f"✗ Empty string name failed: {e}")

# Test 5: Special characters in name
print("\nTesting special characters...")
special_names = ["test>", "<test", "test<>test", "\n", "\t", "🦄", "null\x00byte"]
for name in special_names:
    try:
        s = Sentinel(name)
        expected_repr = f"<{name}>"
        actual_repr = repr(s)
        if actual_repr != expected_repr:
            print(f"✗ Repr mismatch for name={repr(name)}: expected {repr(expected_repr)}, got {repr(actual_repr)}")
        else:
            print(f"✓ Special character handled: {repr(name)}")
    except Exception as e:
        print(f"✗ Failed on special character {repr(name)}: {e}")

# Test 6: Registry clearing edge case
print("\nTesting registry behavior...")
try:
    # Create a sentinel
    s1 = Sentinel("registry_test")
    
    # Manually clear the registry (simulating potential issue)
    Sentinel._existing_instances.clear()
    
    # Try to create the same sentinel again
    s2 = Sentinel("registry_test")
    
    # These should NOT be the same object if registry was cleared
    if s1 is s2:
        print("✗ Potential bug: Sentinels are same object after registry clear")
    else:
        print("✓ Registry clearing creates new objects as expected")
        
    # Now test pickle behavior after registry clear
    pickled = pickle.dumps(s1)
    unpickled = pickle.loads(pickled)
    
    if unpickled is s1:
        print("✗ Unpickled sentinel is same as original after registry clear (unexpected)")
    elif unpickled is s2:
        print("✓ Unpickled sentinel matches new registry entry")
    else:
        print("? Unpickled sentinel is a third object")
        
except Exception as e:
    print(f"✗ Registry test failed: {e}")