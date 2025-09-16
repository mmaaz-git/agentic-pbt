import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

import multi_key_dict
import traceback

def test_bug_scenarios():
    """Test various edge cases that might reveal bugs"""
    bugs_found = []
    
    # Test 1: Unhashable types as keys
    print("Test 1: Testing unhashable types as keys...")
    m = multi_key_dict.multi_key_dict()
    try:
        # Lists are unhashable, this should fail
        m[[1, 2], 'valid_key'] = 'value'
        print("  ✗ Bug: Accepted unhashable list as key!")
        bugs_found.append("Unhashable keys accepted")
    except TypeError as e:
        print(f"  ✓ Correctly rejected unhashable key: {e}")
    except Exception as e:
        print(f"  ? Unexpected error: {e}")
        bugs_found.append(f"Unexpected error with unhashable key: {e}")
    
    # Test 2: Single key as tuple vs non-tuple
    print("\nTest 2: Single key handling...")
    m = multi_key_dict.multi_key_dict()
    try:
        m['single'] = 'value1'
        m[('single',)] = 'value2'  # Should this work or conflict?
        print(f"  m['single'] = {m['single']}")
        print(f"  Set both 'single' and ('single',) - potential issue")
    except Exception as e:
        print(f"  Exception when setting ('single',): {e}")
    
    # Test 3: Empty tuple as keys
    print("\nTest 3: Empty tuple as keys...")
    m = multi_key_dict.multi_key_dict()
    try:
        m[()] = 'empty_tuple_value'
        print("  ✗ Bug: Accepted empty tuple as keys!")
        bugs_found.append("Empty tuple accepted as keys")
    except Exception as e:
        print(f"  ✓ Correctly rejected empty tuple: {e}")
    
    # Test 4: None as a key
    print("\nTest 4: None as key...")
    m = multi_key_dict.multi_key_dict()
    try:
        m[None, 'other'] = 'none_value'
        assert m[None] == 'none_value'
        assert m['other'] == 'none_value'
        print("  ✓ None works as a key")
    except Exception as e:
        print(f"  Issue with None as key: {e}")
        bugs_found.append(f"None as key failed: {e}")
    
    # Test 5: Very large number of keys
    print("\nTest 5: Large number of keys...")
    m = multi_key_dict.multi_key_dict()
    try:
        large_keys = list(range(1000))
        m[tuple(large_keys)] = 'many_keys'
        assert m[500] == 'many_keys'
        print("  ✓ Handled 1000 keys successfully")
    except Exception as e:
        print(f"  Issue with many keys: {e}")
        bugs_found.append(f"Failed with many keys: {e}")
    
    # Test 6: Keys with special strings
    print("\nTest 6: Keys with special strings...")
    m = multi_key_dict.multi_key_dict()
    try:
        # The implementation uses str(type(key)) which could have issues
        m["<class 'int'>", "normal"] = 'special'
        assert m["<class 'int'>"] == 'special'
        print("  ✓ Special string keys work")
    except Exception as e:
        print(f"  Issue with special string: {e}")
        bugs_found.append(f"Special string key failed: {e}")
    
    # Test 7: Duplicate keys in tuple
    print("\nTest 7: Duplicate keys in tuple...")
    m = multi_key_dict.multi_key_dict()
    try:
        m['a', 'a', 'b'] = 'duplicates'
        print(f"  Set with duplicate 'a' in keys")
        print(f"  m['a'] = {m['a']}")
        print(f"  m['b'] = {m['b']}")
        others = m.get_other_keys('a')
        print(f"  get_other_keys('a') = {others}")
        if others.count('a') > 0:
            print("  ✗ Bug: 'a' appears in its own other_keys!")
            bugs_found.append("Duplicate key handling issue")
    except Exception as e:
        print(f"  Exception with duplicate keys: {e}")
    
    # Test 8: Boolean keys (True/False vs 1/0)
    print("\nTest 8: Boolean keys vs integer keys...")
    m = multi_key_dict.multi_key_dict()
    try:
        m[True, 'bool'] = 'true_value'
        m[1, 'int'] = 'one_value'  # In Python, True == 1
        print(f"  Set both True and 1 as keys")
        print(f"  m[True] = {m[True]}")
        print(f"  m[1] = {m[1]}")
        print(f"  m['bool'] = {m['bool']}")
        print(f"  m['int'] = {m['int']}")
    except KeyError as e:
        print(f"  ✓ Correctly raised KeyError for True/1 conflict: {e}")
    except Exception as e:
        print(f"  Unexpected error with bool keys: {e}")
        bugs_found.append(f"Bool/int key issue: {e}")
    
    # Test 9: get() with None value vs non-existent key
    print("\nTest 9: get() with None value...")
    m = multi_key_dict.multi_key_dict()
    m['exists'] = None
    result1 = m.get('exists', 'default')
    result2 = m.get('not_exists', 'default')
    print(f"  m.get('exists', 'default') = {result1}")
    print(f"  m.get('not_exists', 'default') = {result2}")
    if result1 != None:
        print("  ✗ Bug: get() returns default for existing None value!")
        bugs_found.append("get() incorrect with None value")
    
    # Test 10: Update with overlapping key sets
    print("\nTest 10: Update with overlapping key sets...")
    m = multi_key_dict.multi_key_dict()
    try:
        m['a', 'b', 'c'] = 'first'
        m['b', 'c', 'd'] = 'second'  # 'b' and 'c' already mapped
        print("  ✗ Bug: Allowed overlapping key sets!")
        bugs_found.append("Overlapping key sets allowed")
    except KeyError as e:
        print(f"  ✓ Correctly rejected overlapping keys: {e}")
    except Exception as e:
        print(f"  Unexpected error: {e}")
    
    return bugs_found

# Run the tests
print("=" * 60)
print("Bug Hunter for multi_key_dict")
print("=" * 60)

bugs = test_bug_scenarios()

print("\n" + "=" * 60)
if bugs:
    print(f"Found {len(bugs)} potential issue(s):")
    for i, bug in enumerate(bugs, 1):
        print(f"  {i}. {bug}")
else:
    print("No bugs found in the tested scenarios.")
print("=" * 60)