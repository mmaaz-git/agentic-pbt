"""Property-based tests for SQLAlchemy cyextension module."""

import math
from hypothesis import assume, given, strategies as st, settings
import sqlalchemy.cyextension.collections as cyc
import sqlalchemy.cyextension.immutabledict as cyi


# IdentitySet Tests

@given(st.lists(st.integers()))
def test_identityset_length_invariant(values):
    """IdentitySet length should never exceed number of objects added."""
    ids = cyc.IdentitySet()
    for v in values:
        ids.add(v)
    assert len(ids) <= len(values)


@given(st.lists(st.lists(st.integers(), min_size=1, max_size=5)))
def test_identityset_distinct_mutable_objects(lists):
    """Each distinct list object should be in the set, even with same content."""
    ids = cyc.IdentitySet()
    unique_objects = []
    for lst in lists:
        new_list = list(lst)  # Create new list object
        ids.add(new_list)
        unique_objects.append(new_list)
    
    # Each unique object should be in the set
    for obj in unique_objects:
        assert obj in ids
    
    # Length should equal number of unique objects added
    assert len(ids) == len(unique_objects)


@given(
    st.lists(st.integers(), min_size=0, max_size=20),
    st.lists(st.integers(), min_size=0, max_size=20)
)
def test_identityset_set_operations(list_a, list_b):
    """Test that set operations follow set theory laws."""
    # Create objects with controlled identity
    objs_a = [object() for _ in list_a]
    objs_b = [object() for _ in list_b]
    
    ids_a = cyc.IdentitySet(objs_a)
    ids_b = cyc.IdentitySet(objs_b)
    
    # Union properties
    union = ids_a.union(ids_b)
    assert len(union) <= len(ids_a) + len(ids_b)
    assert all(obj in union for obj in ids_a)
    assert all(obj in union for obj in ids_b)
    
    # Intersection properties
    intersection = ids_a.intersection(ids_b)
    assert len(intersection) <= min(len(ids_a), len(ids_b))
    for obj in intersection:
        assert obj in ids_a and obj in ids_b
    
    # Difference properties
    diff = ids_a.difference(ids_b)
    assert len(diff) <= len(ids_a)
    for obj in diff:
        assert obj in ids_a and obj not in ids_b


@given(st.lists(st.integers()))
def test_identityset_copy_independence(values):
    """Copied IdentitySet should be independent of original."""
    ids1 = cyc.IdentitySet()
    for v in values:
        ids1.add(v)
    
    ids2 = ids1.copy()
    
    # Initially should have same contents
    assert len(ids1) == len(ids2)
    
    # Adding to copy shouldn't affect original
    new_obj = object()
    ids2.add(new_obj)
    assert new_obj in ids2
    assert new_obj not in ids1


# OrderedSet Tests

@given(st.lists(st.integers()))
def test_orderedset_preserves_order(values):
    """OrderedSet should preserve insertion order."""
    os = cyc.OrderedSet()
    seen = set()
    expected_order = []
    
    for v in values:
        if v not in seen:
            expected_order.append(v)
            seen.add(v)
        os.add(v)
    
    assert list(os) == expected_order


@given(st.lists(st.integers()))
def test_orderedset_no_duplicates(values):
    """OrderedSet should not contain duplicates."""
    os = cyc.OrderedSet(values)
    os_list = list(os)
    assert len(os_list) == len(set(os_list))


@given(st.lists(st.integers(), min_size=1))
def test_orderedset_first_occurrence_wins(values):
    """When duplicates are added, first occurrence position is preserved."""
    os = cyc.OrderedSet()
    first_positions = {}
    
    for i, v in enumerate(values):
        if v not in first_positions:
            first_positions[v] = i
        os.add(v)
    
    # Check that each value appears at its first occurrence position
    os_list = list(os)
    for i, v in enumerate(os_list):
        # Find first occurrence in original list
        first_idx = values.index(v)
        # Count unique values before this position
        unique_before = len(set(values[:first_idx]))
        assert i == unique_before


@given(
    st.lists(st.integers(), min_size=0, max_size=20),
    st.lists(st.integers(), min_size=0, max_size=20)
)
def test_orderedset_union_preserves_order(list_a, list_b):
    """Union should preserve order from both sets."""
    os_a = cyc.OrderedSet(list_a)
    os_b = cyc.OrderedSet(list_b)
    
    union = os_a.union(os_b)
    union_list = list(union)
    
    # All elements from both sets should be in union
    assert set(union_list) == set(os_a) | set(os_b)
    
    # Elements from os_a should maintain relative order
    a_elements_in_union = [x for x in union_list if x in os_a]
    assert a_elements_in_union == list(os_a)


@given(st.lists(st.integers()))
def test_orderedset_clear_and_readd(values):
    """After clear(), OrderedSet should behave like new."""
    os = cyc.OrderedSet(values)
    os.clear()
    assert len(os) == 0
    assert list(os) == []
    
    # Re-adding should work normally
    if values:
        os.add(values[0])
        assert values[0] in os
        assert len(os) == 1


# immutabledict Tests

@given(st.dictionaries(st.text(), st.integers()))
def test_immutabledict_round_trip(d):
    """Converting dict to immutabledict and back should preserve data."""
    imd = cyi.immutabledict(d)
    assert dict(imd) == d


@given(st.dictionaries(st.text(), st.integers()))
def test_immutabledict_truly_immutable(d):
    """immutabledict should not be modifiable after creation."""
    imd = cyi.immutabledict(d)
    
    # All mutation methods should raise TypeError
    with_error = []
    
    try:
        imd['new_key'] = 42
        with_error.append('setitem')
    except TypeError:
        pass
    
    try:
        imd.update({'another_key': 100})
        with_error.append('update')
    except TypeError:
        pass
    
    try:
        imd.pop('any_key', None)
        with_error.append('pop')
    except TypeError:
        pass
    
    try:
        imd.clear()
        with_error.append('clear')
    except TypeError:
        pass
    
    try:
        imd.setdefault('key', 'value')
        with_error.append('setdefault')
    except TypeError:
        pass
    
    assert with_error == [], f"Methods didn't raise TypeError: {with_error}"


@given(
    st.dictionaries(st.text(), st.integers()),
    st.dictionaries(st.text(), st.integers())
)
def test_immutabledict_union_creates_new(d1, d2):
    """union() should create a new immutabledict with merged contents."""
    imd1 = cyi.immutabledict(d1)
    imd2 = cyi.immutabledict(d2)
    
    result = imd1.union(imd2)
    
    # Result should be a new immutabledict
    assert isinstance(result, cyi.immutabledict)
    assert result is not imd1
    assert result is not imd2
    
    # Result should have merged contents (d2 overrides d1)
    expected = dict(d1)
    expected.update(d2)
    assert dict(result) == expected
    
    # Original dicts should be unchanged
    assert dict(imd1) == d1
    assert dict(imd2) == d2


@given(
    st.dictionaries(st.text(), st.integers()),
    st.dictionaries(st.text(), st.integers())
)
def test_immutabledict_merge_with(d1, d2):
    """merge_with() should behave like union()."""
    imd1 = cyi.immutabledict(d1)
    imd2 = cyi.immutabledict(d2)
    
    result_union = imd1.union(imd2)
    result_merge = imd1.merge_with(imd2)
    
    # Both methods should produce the same result
    assert dict(result_union) == dict(result_merge)


@given(st.dictionaries(st.text(), st.integers()))
def test_immutabledict_get_method(d):
    """get() method should work like regular dict."""
    imd = cyi.immutabledict(d)
    
    for key in d:
        assert imd.get(key) == d.get(key)
    
    # Test with non-existent key
    assert imd.get('_nonexistent_key_') is None
    assert imd.get('_nonexistent_key_', 'default') == 'default'


@given(st.dictionaries(st.text(), st.integers(), min_size=1))
def test_immutabledict_items_keys_values(d):
    """items(), keys(), values() should work like regular dict."""
    imd = cyi.immutabledict(d)
    
    assert set(imd.keys()) == set(d.keys())
    assert set(imd.values()) == set(d.values())
    assert set(imd.items()) == set(d.items())


@given(st.lists(st.text(), min_size=1), st.integers())
def test_immutabledict_fromkeys(keys, value):
    """fromkeys() should create new immutabledict."""
    result = cyi.immutabledict.fromkeys(keys, value)
    
    assert isinstance(result, cyi.immutabledict)
    for key in set(keys):
        assert key in result
        assert result[key] == value


# Edge case tests

@given(st.integers())
def test_identityset_singleton_behavior(value):
    """Single value added multiple times should appear once."""
    ids = cyc.IdentitySet()
    ids.add(value)
    ids.add(value)
    ids.add(value)
    assert len(ids) == 1
    assert value in ids


@given(st.lists(st.integers()))
def test_orderedset_pop_removes_last(values):
    """pop() should remove and return the last element."""
    assume(len(values) > 0)
    os = cyc.OrderedSet(values)
    original_len = len(os)
    
    if original_len > 0:
        last_elem = list(os)[-1]
        popped = os.pop()
        assert popped == last_elem
        assert len(os) == original_len - 1
        assert popped not in os


@given(st.integers(), st.integers(min_value=0, max_value=10))
def test_orderedset_insert_method(value, position):
    """insert() should add element at specific position if not present."""
    os = cyc.OrderedSet([1, 2, 3, 4, 5])
    original = list(os)
    
    if value not in os:
        os.insert(position, value)
        new_list = list(os)
        
        # Value should be inserted
        assert value in os
        
        # Check position
        if position <= len(original):
            actual_pos = new_list.index(value)
            # Count how many elements before position are still before value
            elements_before = original[:position]
            still_before = [x for x in new_list[:actual_pos] if x in elements_before]
            assert len(still_before) == len(elements_before)
    else:
        # If value already exists, insert should not change anything
        os.insert(position, value)
        assert list(os) == original


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])