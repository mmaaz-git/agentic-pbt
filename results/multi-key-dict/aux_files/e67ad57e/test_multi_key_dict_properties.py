import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/multi-key-dict_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import multi_key_dict
import pytest

# Strategy for generating keys of various types
key_strategy = st.one_of(
    st.integers(),
    st.text(min_size=1, max_size=20),
    st.floats(allow_nan=False, allow_infinity=False),
    st.tuples(st.integers(), st.integers()),  # hashable tuples
)

# Strategy for values
value_strategy = st.one_of(
    st.integers(),
    st.text(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.none(),
    st.lists(st.integers(), max_size=5),
)

@given(
    keys=st.lists(key_strategy, min_size=2, max_size=5, unique=True),
    value=value_strategy
)
def test_multi_key_all_keys_retrieve_same_value(keys, value):
    """Property: All keys in a multi-key mapping should retrieve the same value"""
    m = multi_key_dict.multi_key_dict()
    
    # Set multiple keys to same value
    m[tuple(keys)] = value
    
    # All keys should retrieve the same value
    retrieved_values = [m[k] for k in keys]
    assert all(v == value for v in retrieved_values), f"Not all keys retrieve same value: {retrieved_values}"


@given(
    keys=st.lists(key_strategy, min_size=2, max_size=5, unique=True),
    value=value_strategy,
    update_key_idx=st.integers(min_value=0)
)
def test_multi_key_update_affects_all_keys(keys, value, update_key_idx):
    """Property: Updating via one key should update value for all keys"""
    assume(len(keys) >= 2)
    update_key_idx = update_key_idx % len(keys)
    
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    # Update via one key
    new_value = "updated_value"
    m[keys[update_key_idx]] = new_value
    
    # All keys should now retrieve the new value
    for k in keys:
        assert m[k] == new_value, f"Key {k} did not get updated value"


@given(
    keys=st.lists(key_strategy, min_size=2, max_size=5, unique=True),
    value=value_strategy,
    query_key_idx=st.integers(min_value=0)
)
def test_get_other_keys_returns_correct_keys(keys, value, query_key_idx):
    """Property: get_other_keys should return all other keys mapping to same value"""
    assume(len(keys) >= 2)
    query_key_idx = query_key_idx % len(keys)
    
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    query_key = keys[query_key_idx]
    other_keys = m.get_other_keys(query_key)
    
    # Should return all keys except the query key
    expected_other_keys = [k for k in keys if k != query_key]
    assert set(other_keys) == set(expected_other_keys), f"get_other_keys returned {other_keys}, expected {expected_other_keys}"
    
    # With including_current=True, should return all keys
    all_keys = m.get_other_keys(query_key, including_current=True)
    assert set(all_keys) == set(keys), f"get_other_keys(including_current=True) returned {all_keys}, expected {keys}"


@given(
    mappings=st.lists(
        st.tuples(
            st.lists(key_strategy, min_size=1, max_size=3, unique=True),
            value_strategy
        ),
        min_size=0,
        max_size=10
    )
)
def test_length_equals_number_of_values(mappings):
    """Property: Length should equal the number of unique value mappings"""
    m = multi_key_dict.multi_key_dict()
    
    # Add all mappings, ensuring no key conflicts
    used_keys = set()
    expected_length = 0
    
    for keys, value in mappings:
        # Skip if any key already used (to avoid conflicts)
        if any(k in used_keys for k in keys):
            continue
        
        if len(keys) == 1:
            m[keys[0]] = value
        else:
            m[tuple(keys)] = value
        
        used_keys.update(keys)
        expected_length += 1
    
    assert len(m) == expected_length, f"Length {len(m)} != expected {expected_length}"


@given(
    keys=st.lists(key_strategy, min_size=2, max_size=5, unique=True),
    value=value_strategy,
    delete_key_idx=st.integers(min_value=0)
)
def test_deletion_removes_all_associated_keys(keys, value, delete_key_idx):
    """Property: Deleting via one key should remove all associated keys"""
    assume(len(keys) >= 2)
    delete_key_idx = delete_key_idx % len(keys)
    
    m = multi_key_dict.multi_key_dict()
    m[tuple(keys)] = value
    
    # Delete using one key
    del m[keys[delete_key_idx]]
    
    # None of the keys should exist anymore
    for k in keys:
        assert k not in m, f"Key {k} still exists after deletion"
        
        # Should raise KeyError when trying to access
        with pytest.raises(KeyError):
            _ = m[k]


@given(
    existing_keys=st.lists(key_strategy, min_size=1, max_size=3, unique=True),
    new_keys=st.lists(key_strategy, min_size=1, max_size=3, unique=True),
    value1=value_strategy,
    value2=value_strategy
)
def test_cannot_add_conflicting_multi_key_mappings(existing_keys, new_keys, value1, value2):
    """Property: Cannot create new multi-key mapping if one key already exists with different value"""
    assume(value1 != value2)  # Only test when values are different
    
    m = multi_key_dict.multi_key_dict()
    
    # Add first mapping
    if len(existing_keys) == 1:
        m[existing_keys[0]] = value1
    else:
        m[tuple(existing_keys)] = value1
    
    # Try to add new mapping that includes an existing key
    # This should fail if any existing key is in new_keys
    overlap = set(existing_keys) & set(new_keys)
    
    if overlap and len(new_keys) > 1:
        # Should raise KeyError when trying to create conflicting mapping
        with pytest.raises(KeyError):
            m[tuple(new_keys)] = value2
    else:
        # No conflict, should work fine
        if len(new_keys) == 1:
            m[new_keys[0]] = value2 if new_keys[0] not in existing_keys else value1
        else:
            m[tuple(new_keys)] = value2


@given(
    key=key_strategy,
    value=value_strategy,
    default=value_strategy
)
def test_get_method_behavior(key, value, default):
    """Property: get() method should behave like dict.get()"""
    m = multi_key_dict.multi_key_dict()
    
    # Test get on non-existing key
    assert m.get(key) is None, "get() should return None for non-existing key"
    assert m.get(key, default) == default, "get() should return default for non-existing key"
    
    # Add the key
    m[key] = value
    
    # Test get on existing key
    assert m.get(key) == value, "get() should return value for existing key"
    assert m.get(key, default) == value, "get() should return value (not default) for existing key"


@given(
    keys1=st.lists(key_strategy, min_size=1, max_size=3, unique=True),
    keys2=st.lists(key_strategy, min_size=1, max_size=3, unique=True),
    value=value_strategy
)
def test_update_multi_key_to_same_value_allowed(keys1, keys2, value):
    """Property: Can update multi-key mapping if all keys map to same value"""
    m = multi_key_dict.multi_key_dict()
    
    # Create initial mapping
    all_keys = keys1 + keys2
    if len(all_keys) == 1:
        m[all_keys[0]] = value
    else:
        m[tuple(all_keys)] = value
    
    # Should be able to update using subset of keys
    if len(keys1) == 1:
        m[keys1[0]] = value  # Same value, should work
    else:
        m[tuple(keys1)] = value  # Same value, should work
    
    # All original keys should still work
    for k in all_keys:
        assert k in m, f"Key {k} should still exist"
        assert m[k] == value, f"Key {k} should still map to same value"


@given(st.data())
def test_contains_consistency(data):
    """Property: __contains__ should be consistent with has_key and get"""
    m = multi_key_dict.multi_key_dict()
    
    # Generate some random mappings
    for _ in range(data.draw(st.integers(0, 10))):
        keys = data.draw(st.lists(key_strategy, min_size=1, max_size=3, unique=True))
        value = data.draw(value_strategy)
        
        # Skip if key conflict
        if any(k in m for k in keys):
            continue
            
        if len(keys) == 1:
            m[keys[0]] = value
        else:
            m[tuple(keys)] = value
    
    # Test consistency for random keys
    for _ in range(20):
        test_key = data.draw(key_strategy)
        
        # These should all be consistent
        contains_result = test_key in m
        has_key_result = m.has_key(test_key)
        get_result = m.get(test_key) is not None
        
        if contains_result:
            assert has_key_result, "__contains__ and has_key disagree"
            assert get_result, "__contains__ and get disagree"
        else:
            assert not has_key_result, "__contains__ and has_key disagree"
            # Note: get could return None as a value, so we can't always check this