#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import multi_key_dict
import traceback

print("=" * 70)
print("Hypothesis-based Bug Finder for multi_key_dict")
print("=" * 70)

# Track found bugs
bugs_found = []

# Test 1: Boolean vs Integer key collision
print("\n[Test 1] Boolean vs Integer key collision...")
try:
    m = multi_key_dict.multi_key_dict()
    # In Python, True == 1 and False == 0, but they are different types
    m[True, 'a'] = 'bool_value'
    
    # Now try to add 1 with a different key
    try:
        m[1, 'b'] = 'int_value'
        # If this succeeds, there might be an issue
        print(f"  Added both True and 1 as separate multi-keys")
        print(f"  m[True] = {m[True]}")
        print(f"  m[1] = {m[1]}")
        print(f"  m['a'] = {m['a']}")
        print(f"  m['b'] = {m['b']}")
        
        # Check if they're treated as same or different
        if m[True] == m[1] and m['a'] != m['b']:
            print("  ✗ BUG FOUND: True and 1 are conflated but create separate mappings!")
            bugs_found.append({
                'test': 'Boolean/Integer collision',
                'description': 'True and 1 are treated inconsistently',
                'severity': 'Medium'
            })
    except KeyError as e:
        print(f"  ✓ Correctly rejected: {e}")
except Exception as e:
    print(f"  Unexpected error: {e}")
    traceback.print_exc()

# Test 2: Hash collision with custom objects
print("\n[Test 2] Testing with objects that have same hash...")
class SameHash:
    def __init__(self, value):
        self.value = value
    def __hash__(self):
        return 42  # Always same hash
    def __eq__(self, other):
        return isinstance(other, SameHash) and self.value == other.value
    def __repr__(self):
        return f"SameHash({self.value})"

try:
    m = multi_key_dict.multi_key_dict()
    obj1 = SameHash(1)
    obj2 = SameHash(2)
    
    m[obj1, 'a'] = 'value1'
    m[obj2, 'b'] = 'value2'
    
    print(f"  Added two objects with same hash as different keys")
    print(f"  m[obj1] = {m[obj1]}")
    print(f"  m[obj2] = {m[obj2]}")
    print("  ✓ Handles hash collisions correctly")
except Exception as e:
    print(f"  Issue with hash collision: {e}")

# Test 3: Single element tuple ambiguity
print("\n[Test 3] Single element tuple ambiguity...")
try:
    m = multi_key_dict.multi_key_dict()
    
    # Set with string key
    m['key'] = 'value1'
    
    # Try to set with single-element tuple
    try:
        m[('key',)] = 'value2'
        print(f"  Set both 'key' and ('key',)")
        print(f"  m['key'] = {m['key']}")
        
        # Are they the same or different?
        if 'key' in m and ('key',) in m:
            print("  Note: 'key' and ('key',) are treated as different keys")
    except KeyError:
        print("  'key' and ('key',) conflict as expected")
        
except Exception as e:
    print(f"  Error: {e}")

# Test 4: Property test - deletion consistency
@given(
    keys=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=2, max_size=5, unique=True),
    value=st.integers(),
    del_idx=st.integers(min_value=0, max_value=4)
)
@settings(max_examples=200, deadline=None)
def test_deletion_consistency(keys, value, del_idx):
    del_idx = del_idx % len(keys)
    
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    # Store other keys before deletion
    other_keys_before = set(m.get_other_keys(keys[del_idx], including_current=True))
    
    # Delete using one key
    del m[keys[del_idx]]
    
    # Check all keys are gone
    for k in keys:
        if k in m:
            raise AssertionError(f"Key {k} still exists after deletion")

print("\n[Test 4] Property: Deletion consistency...")
try:
    test_deletion_consistency()
    print("  ✓ Deletion is consistent across all keys")
except AssertionError as e:
    print(f"  ✗ BUG FOUND: {e}")
    bugs_found.append({
        'test': 'Deletion consistency',
        'description': str(e),
        'severity': 'High'
    })
except Exception as e:
    print(f"  Error during testing: {e}")

# Test 5: Property test - get_other_keys correctness
@given(
    keys=st.lists(st.one_of(st.integers(), st.text(min_size=1, max_size=5)), 
                  min_size=2, max_size=5, unique=True),
    value=st.integers()
)
@settings(max_examples=200, deadline=None)
def test_get_other_keys_correctness(keys, value):
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    for key in keys:
        others = m.get_other_keys(key)
        others_with_current = m.get_other_keys(key, including_current=True)
        
        # Check that others doesn't include the query key
        if key in others:
            raise AssertionError(f"get_other_keys({key}) includes the key itself")
        
        # Check that others_with_current does include it
        if key not in others_with_current:
            raise AssertionError(f"get_other_keys({key}, True) doesn't include the key")
        
        # Check that all other keys are present
        expected_others = set(keys) - {key}
        if set(others) != expected_others:
            raise AssertionError(f"get_other_keys({key}) returned {others}, expected {expected_others}")

print("\n[Test 5] Property: get_other_keys correctness...")
try:
    test_get_other_keys_correctness()
    print("  ✓ get_other_keys works correctly")
except AssertionError as e:
    print(f"  ✗ BUG FOUND: {e}")
    bugs_found.append({
        'test': 'get_other_keys correctness',
        'description': str(e),
        'severity': 'Medium'
    })
except Exception as e:
    print(f"  Error during testing: {e}")

# Test 6: Stress test with many operations
print("\n[Test 6] Stress test with many operations...")
@given(st.data())
@settings(max_examples=100, deadline=None)
def test_stress_operations(data):
    m = multi_key_dict.multi_key_dict()
    used_keys = set()
    
    for _ in range(10):
        # Generate unique keys
        keys = []
        for _ in range(data.draw(st.integers(1, 4))):
            key = data.draw(st.one_of(
                st.integers(min_value=-100, max_value=100),
                st.text(min_size=1, max_size=3)
            ))
            if key not in used_keys:
                keys.append(key)
                used_keys.add(key)
        
        if len(keys) == 0:
            continue
            
        value = data.draw(st.integers())
        
        # Add to dictionary
        if len(keys) == 1:
            m[keys[0]] = value
        else:
            m[tuple(keys)] = value
        
        # Verify all keys work
        for k in keys:
            if m[k] != value:
                raise AssertionError(f"Key {k} doesn't return correct value")

try:
    test_stress_operations()
    print("  ✓ Stress test passed")
except AssertionError as e:
    print(f"  ✗ BUG FOUND: {e}")
    bugs_found.append({
        'test': 'Stress test',
        'description': str(e),
        'severity': 'High'
    })
except Exception as e:
    print(f"  Error during testing: {e}")

# Test 7: Edge case - using dictionary internal attributes as keys
print("\n[Test 7] Using internal attribute names as keys...")
try:
    m = multi_key_dict.multi_key_dict()
    
    # These are internal attributes used by multi_key_dict
    dangerous_keys = ['items_dict', '__dict__', '__class__', '__module__']
    
    for key in dangerous_keys:
        try:
            m[key] = f'value_for_{key}'
            retrieved = m[key]
            print(f"  Set and retrieved '{key}': {retrieved}")
        except Exception as e:
            print(f"  Error with key '{key}': {e}")
            bugs_found.append({
                'test': 'Internal attribute collision',
                'description': f"Cannot use '{key}' as a key: {e}",
                'severity': 'Low'
            })
    
except Exception as e:
    print(f"  Unexpected error: {e}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if bugs_found:
    print(f"\nFound {len(bugs_found)} bug(s):\n")
    for i, bug in enumerate(bugs_found, 1):
        print(f"{i}. [{bug['severity']}] {bug['test']}")
        print(f"   {bug['description']}\n")
else:
    print("\nNo bugs found! All tests passed ✓")

print("=" * 70)