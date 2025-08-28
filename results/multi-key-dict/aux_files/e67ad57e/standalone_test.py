#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, Verbosity
import multi_key_dict

print("Testing multi_key_dict properties...")
print("=" * 60)

# Test 1: All keys retrieve same value
@given(
    keys=st.lists(st.integers(), min_size=2, max_size=5, unique=True),
    value=st.integers()
)
@settings(max_examples=100, verbosity=Verbosity.verbose)
def test_multi_key_all_keys_retrieve_same_value(keys, value):
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    retrieved_values = [m[k] for k in keys]
    assert all(v == value for v in retrieved_values), f"Not all keys retrieve same value: {retrieved_values}"

print("\nTest 1: Testing that all keys in multi-key mapping retrieve same value...")
try:
    test_multi_key_all_keys_retrieve_same_value()
    print("✓ Test 1 passed")
except Exception as e:
    print(f"✗ Test 1 failed: {e}")

# Test 2: get_other_keys returns correct keys
@given(
    keys=st.lists(st.integers(), min_size=2, max_size=5, unique=True),
    value=st.integers(),
    query_idx=st.integers(min_value=0, max_value=4)
)
@settings(max_examples=100)
def test_get_other_keys(keys, value, query_idx):
    assume(len(keys) >= 2)
    query_idx = query_idx % len(keys)
    
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    query_key = keys[query_idx]
    other_keys = m.get_other_keys(query_key)
    expected = [k for k in keys if k != query_key]
    
    assert set(other_keys) == set(expected), f"get_other_keys returned {other_keys}, expected {expected}"

print("\nTest 2: Testing get_other_keys method...")
try:
    test_get_other_keys()
    print("✓ Test 2 passed")
except Exception as e:
    print(f"✗ Test 2 failed: {e}")

# Test 3: Deletion removes all keys
@given(
    keys=st.lists(st.integers(), min_size=2, max_size=5, unique=True),
    value=st.integers(),
    del_idx=st.integers(min_value=0, max_value=4)
)
@settings(max_examples=100)
def test_deletion(keys, value, del_idx):
    assume(len(keys) >= 2)
    del_idx = del_idx % len(keys)
    
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    del m[keys[del_idx]]
    
    for k in keys:
        assert k not in m, f"Key {k} still exists after deletion"

print("\nTest 3: Testing deletion removes all associated keys...")
try:
    test_deletion()
    print("✓ Test 3 passed")
except Exception as e:
    print(f"✗ Test 3 failed: {e}")

# Test 4: Complex key types (tuples as keys)
@given(
    keys=st.lists(
        st.tuples(st.integers(), st.integers()),
        min_size=2, max_size=4, unique=True
    ),
    value=st.text()
)
@settings(max_examples=50)
def test_tuple_keys(keys, value):
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    for k in keys:
        assert m[k] == value, f"Tuple key {k} doesn't retrieve correct value"

print("\nTest 4: Testing with tuple keys...")
try:
    test_tuple_keys()
    print("✓ Test 4 passed")
except Exception as e:
    print(f"✗ Test 4 failed: {e}")

# Test 5: Mixed type keys
@given(
    int_key=st.integers(),
    str_key=st.text(min_size=1, max_size=10),
    float_key=st.floats(allow_nan=False, allow_infinity=False),
    value=st.integers()
)
@settings(max_examples=50)
def test_mixed_type_keys(int_key, str_key, float_key, value):
    m = multi_key_dict.multi_key_dict()
    keys = [int_key, str_key, float_key]
    
    m[tuple(keys)] = value
    
    assert m[int_key] == value
    assert m[str_key] == value  
    assert m[float_key] == value

print("\nTest 5: Testing with mixed type keys...")
try:
    test_mixed_type_keys()
    print("✓ Test 5 passed")
except Exception as e:
    print(f"✗ Test 5 failed: {e}")

print("\n" + "=" * 60)
print("All property tests completed!")