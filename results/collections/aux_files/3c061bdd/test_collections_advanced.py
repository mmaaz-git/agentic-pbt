import math
import sys
from collections.abc import Set, MutableSet, Sequence, MutableSequence, MutableMapping, Mapping
from hypothesis import given, strategies as st, settings, assume, example
import pytest


# Let's look for edge cases and boundary conditions

class MySet(Set):
    def __init__(self, data=()):
        self._data = set(data) if not isinstance(data, set) else data
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)
    
    def __repr__(self):
        return f"MySet({self._data})"


class MyMutableSet(MutableSet):
    def __init__(self, data=()):
        self._data = set(data) if not isinstance(data, set) else data
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        return iter(self._data) 
    
    def __len__(self):
        return len(self._data)
    
    def add(self, item):
        self._data.add(item)
    
    def discard(self, item):
        self._data.discard(item)


class MyMutableMapping(MutableMapping):
    def __init__(self, data=None):
        self._data = dict(data) if data else {}
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value
    
    def __delitem__(self, key):
        del self._data[key]
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)


# Test the _hash function edge cases 
@given(st.lists(st.integers()))
def test_set_hash_edge_cases(data):
    s = MySet(data)
    h = s._hash()
    
    # Hash should be an integer
    assert isinstance(h, int)
    
    # Hash should be consistent
    h2 = s._hash()
    assert h == h2
    
    # Hash value should be within sys.maxsize bounds (as per implementation)
    assert -sys.maxsize - 1 <= h <= sys.maxsize


# Test hash with special value -1
def test_set_hash_negative_one():
    # The implementation has special handling for -1
    # Let's create sets that might produce -1 hash
    
    # Create multiple sets and check their hashes
    sets_to_test = [
        MySet([]),
        MySet([0]),
        MySet([-1]),
        MySet([1, 2, 3]),
        MySet(range(100)),
    ]
    
    for s in sets_to_test:
        h = s._hash()
        # According to the code, if h == -1, it should be changed to 590923713
        # Let's verify this never returns -1
        assert h != -1


# Test Set operations with non-Set iterables (allowed by the implementation)
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_operations_with_lists(data1, data2):
    s1 = MySet(data1)
    
    # The & operator should work with any iterable
    result = s1 & data2  # Pass a list, not a Set
    
    # Result should only contain elements in both
    for elem in result:
        assert elem in s1
        assert elem in data2


# Test MutableSet operations edge cases
@given(st.lists(st.integers()))
def test_mutableset_pop_empty_raises(data):
    ms = MyMutableSet(data)
    
    # Pop all elements
    while len(ms) > 0:
        ms.pop()
    
    # Now pop on empty should raise KeyError
    with pytest.raises(KeyError):
        ms.pop()


# Test MutableMapping update with different input types
@given(st.dictionaries(st.text(), st.integers()),
       st.dictionaries(st.text(), st.integers()))
def test_mutablemapping_update_types(dict1, dict2):
    m = MyMutableMapping(dict1)
    original_keys = set(m.keys())
    
    # Test update with dict
    m.update(dict2)
    
    # All keys from dict2 should be in m
    for key in dict2:
        assert key in m
        assert m[key] == dict2[key]


# Test MutableMapping update with an object that has keys() method
class KeysObject:
    def __init__(self, data):
        self._data = data
    
    def keys(self):
        return self._data.keys()
    
    def __getitem__(self, key):
        return self._data[key]


@given(st.dictionaries(st.text(), st.integers()))
def test_mutablemapping_update_with_keys_object(data):
    m = MyMutableMapping()
    ko = KeysObject(data)
    
    m.update(ko)
    
    for key in data:
        assert key in m
        assert m[key] == data[key]


# Test Set comparison edge cases
@given(st.lists(st.integers()))
def test_set_comparison_with_self(data):
    s = MySet(data)
    
    # All comparisons with self should work correctly
    assert s <= s
    assert s >= s
    assert s == s
    assert not (s < s)
    assert not (s > s)


# Test sequence index with edge case boundaries
class MySequence(Sequence):
    def __init__(self, data):
        self._data = list(data)
    
    def __getitem__(self, index):
        return self._data[index]
    
    def __len__(self):
        return len(self._data)


@given(st.lists(st.integers(), min_size=2))
def test_sequence_index_boundaries(data):
    seq = MySequence(data)
    value = data[0]
    
    # Test with stop = 0 (should not find anything)
    with pytest.raises(ValueError):
        seq.index(value, start=0, stop=0)
    
    # Test with negative stop
    idx = seq.index(value, start=0, stop=-1)
    # Should only search up to but not including the last element
    assert idx < len(data) - 1


# Test MutableSequence reverse with single element
def test_mutablesequence_reverse_single():
    class MyMutableSeq(MutableSequence):
        def __init__(self, data):
            self._data = list(data)
        
        def __getitem__(self, index):
            return self._data[index]
        
        def __setitem__(self, index, value):
            self._data[index] = value
        
        def __delitem__(self, index):
            del self._data[index]
        
        def __len__(self):
            return len(self._data)
        
        def insert(self, index, value):
            self._data.insert(index, value)
    
    seq = MyMutableSeq([42])
    seq.reverse()
    assert list(seq) == [42]


# Test Set XOR with non-Set iterable
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_xor_with_iterable(data1, data2):
    s1 = MySet(data1)
    result = s1 ^ data2  # XOR with a list
    
    # Should work and give symmetric difference
    set1 = set(data1)
    set2 = set(data2)
    expected = (set1 - set2) | (set2 - set1)
    
    assert set(result) == expected


# Test edge case: empty set hash
def test_empty_set_hash():
    s1 = MySet([])
    s2 = MySet([])
    
    h1 = s1._hash()
    h2 = s2._hash()
    
    # Empty sets should have the same hash
    assert h1 == h2
    
    # Should be deterministic
    assert h1 == 590923713  # Based on the algorithm for n=0


# Look for overflow issues in hash computation
@given(st.lists(st.integers(min_value=-sys.maxsize, max_value=sys.maxsize)))
def test_set_hash_overflow(data):
    s = MySet(data)
    h = s._hash()
    
    # Should not raise any exceptions
    assert isinstance(h, int)
    
    # Should be within bounds
    assert -sys.maxsize - 1 <= h <= sys.maxsize


# Test MutableMapping popitem on empty
def test_mutablemapping_popitem_empty():
    m = MyMutableMapping()
    
    with pytest.raises(KeyError):
        m.popitem()


# Test mapping equality
@given(st.dictionaries(st.text(), st.integers()))
def test_mapping_equality(data):
    m1 = MyMutableMapping(data)
    m2 = MyMutableMapping(data)
    
    # Should be equal if they have the same items
    assert m1 == m2
    
    # Modify one and they should not be equal
    if len(data) > 0:
        key = next(iter(data))
        m2[key] = m2[key] + 1
        assert m1 != m2


# Test MutableSet remove on missing element
@given(st.lists(st.integers()), st.integers())
def test_mutableset_remove_missing(data, value):
    ms = MyMutableSet(data)
    assume(value not in data)
    
    with pytest.raises(KeyError):
        ms.remove(value)


# Check for interesting behavior in set operations
@given(st.lists(st.integers()))
def test_set_symmetric_operations(data):
    s = MySet(data)
    
    # Test __rand__, __ror__, __rxor__ are properly defined
    # These should work with the set on the right side
    result1 = data & s  # Should call s.__rand__
    result2 = data | s  # Should call s.__ror__
    result3 = data ^ s  # Should call s.__rxor__
    
    # Verify they give correct results
    data_set = set(data)
    s_set = set(s)
    
    assert set(result1) == data_set & s_set
    assert set(result2) == data_set | s_set
    assert set(result3) == data_set ^ s_set


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])