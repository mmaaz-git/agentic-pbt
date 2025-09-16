import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

import multi_key_dict

# Simple manual test to check for basic bugs
print("Running simple manual tests...")

# Test 1: Basic multi-key functionality
m = multi_key_dict.multi_key_dict()
m['a', 'b', 'c'] = 'value1'
print(f"Test 1 - Basic multi-key: m['a'] = {m['a']}, m['b'] = {m['b']}, m['c'] = {m['c']}")
assert m['a'] == 'value1'
assert m['b'] == 'value1'
assert m['c'] == 'value1'
print("✓ Test 1 passed")

# Test 2: Update through one key
m['a'] = 'value2'
print(f"Test 2 - Update via one key: m['a'] = {m['a']}, m['b'] = {m['b']}, m['c'] = {m['c']}")
assert m['a'] == 'value2'
assert m['b'] == 'value2'
assert m['c'] == 'value2'
print("✓ Test 2 passed")

# Test 3: get_other_keys
others = m.get_other_keys('a')
print(f"Test 3 - get_other_keys('a'): {others}")
assert set(others) == {'b', 'c'}
print("✓ Test 3 passed")

# Test 4: Test with empty string key
m2 = multi_key_dict.multi_key_dict()
try:
    m2['', 'b'] = 'test'
    print(f"Test 4 - Empty string key: m2[''] = {m2['']}, m2['b'] = {m2['b']}")
    assert m2[''] == 'test'
    assert m2['b'] == 'test'
    print("✓ Test 4 passed")
except Exception as e:
    print(f"✗ Test 4 failed: {e}")

# Test 5: Test with None as value
m3 = multi_key_dict.multi_key_dict()
m3['x', 'y'] = None
print(f"Test 5 - None value: m3['x'] = {m3['x']}, m3['y'] = {m3['y']}")
assert m3['x'] is None
assert m3['y'] is None
print("✓ Test 5 passed")

# Test 6: Test deletion
del m3['x']
print(f"Test 6 - After deletion: 'x' in m3 = {'x' in m3}, 'y' in m3 = {'y' in m3}")
assert 'x' not in m3
assert 'y' not in m3
print("✓ Test 6 passed")

print("\nAll simple tests passed!")