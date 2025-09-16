import sys
import math
from collections.abc import Set, MutableSet, Sequence, MutableSequence, MutableMapping, ItemsView
from hypothesis import given, strategies as st, settings, assume, example
import pytest


# Look for more complex bugs and edge cases

class MySet(Set):
    def __init__(self, data=()):
        self._data = set(data) if not isinstance(data, set) else data
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)


# Test ItemsView __contains__ with value comparison
class MyMapping(MutableMapping):
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


# Check ItemsView behavior with NaN values
def test_itemsview_nan_comparison():
    m = MyMapping()
    m['key'] = float('nan')
    
    items = m.items()
    
    # NaN is not equal to itself, but 'is' comparison should work
    # The implementation uses "v is value or v == value"
    nan_value = float('nan')
    
    # This should return False because nan != nan
    result = ('key', nan_value) in items
    assert result is False
    
    # But with the same NaN object, it should work due to 'is' check
    actual_nan = m['key']
    result2 = ('key', actual_nan) in items
    assert result2 is True


# Test interesting properties of Set operations with non-hashable elements
class UnhashableSet(Set):
    """A Set that can contain unhashable elements for testing"""
    def __init__(self, data=()):
        self._data = list(data)  # Use list to allow unhashable
    
    def __contains__(self, item):
        for elem in self._data:
            try:
                if elem is item or elem == item:
                    return True
            except:
                pass
        return False
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)


# Test hash computation with unhashable elements
def test_set_hash_with_unhashable():
    # If we try to hash a set containing unhashable elements, it should fail
    s = UnhashableSet([[1, 2], [3, 4]])  # Lists are unhashable
    
    with pytest.raises(TypeError):
        s._hash()


# Test MutableSequence.reverse with odd implementation edge case
class CustomMutableSeq(MutableSequence):
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


@given(st.lists(st.floats(allow_nan=True, allow_infinity=True)))
def test_sequence_contains_with_nan(data):
    # Test sequence __contains__ with NaN values
    class MySeq(Sequence):
        def __init__(self, data):
            self._data = list(data)
        
        def __getitem__(self, index):
            return self._data[index]
        
        def __len__(self):
            return len(self._data)
    
    seq = MySeq(data)
    
    # Check if NaN handling is correct
    for i, val in enumerate(data):
        if math.isnan(val):
            # NaN should be found using 'is' comparison
            assert seq._data[i] in seq  # Using the actual object
            
            # But a different NaN should not be found
            other_nan = float('nan')
            # This is interesting - the implementation uses "v is value or v == value"
            # So different NaN objects won't be equal
            assert other_nan not in seq


# Test Set operations return types
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_operations_return_types(data1, data2):
    s1 = MySet(data1)
    s2 = MySet(data2)
    
    # All these operations should return the same type as s1
    intersection = s1 & s2
    assert type(intersection) == type(s1)
    
    union = s1 | s2
    assert type(union) == type(s1)
    
    difference = s1 - s2
    assert type(difference) == type(s1)
    
    xor = s1 ^ s2
    assert type(xor) == type(s1)


# Test MutableMapping.update with iterator of pairs
@given(st.lists(st.tuples(st.text(), st.integers())))
def test_mutablemapping_update_with_iterator(pairs):
    m = MyMapping()
    
    # Update with an iterator of (key, value) pairs
    m.update(pairs)
    
    # All pairs should be in the mapping
    for key, value in pairs:
        assert key in m
        assert m[key] == value


# Test MutableMapping.update with conflicting sources
@given(st.dictionaries(st.text(min_size=1), st.integers()),
       st.dictionaries(st.text(min_size=1), st.integers()))
def test_mutablemapping_update_order(dict1, dict2):
    # Get a common key if exists
    common_keys = set(dict1.keys()) & set(dict2.keys())
    
    m = MyMapping()
    
    # Update should apply in order: other, then kwargs
    m.update(dict1, **dict2)
    
    # dict2 (kwargs) should override dict1 values for common keys
    for key in common_keys:
        assert m[key] == dict2[key]
    
    # All keys should be present
    for key in dict1:
        assert key in m
    for key in dict2:
        assert key in m
        assert m[key] == dict2[key]  # kwargs win


# Edge case: Sequence.index with None stop
@given(st.lists(st.integers(), min_size=1))
def test_sequence_index_none_stop(data):
    class MySeq(Sequence):
        def __init__(self, data):
            self._data = list(data)
        
        def __getitem__(self, index):
            return self._data[index]
        
        def __len__(self):
            return len(self._data)
    
    seq = MySeq(data)
    value = data[0]
    
    # None stop should search to the end
    idx1 = seq.index(value, 0, None)
    idx2 = seq.index(value, 0, len(data))
    idx3 = seq.index(value, 0)  # No stop
    
    assert idx1 == idx2 == idx3


# Check MutableSet behavior with iterator modification
def test_mutableset_clear_implementation():
    # The clear() method uses pop() in a loop
    # Let's verify it works correctly
    
    class TrackingMutableSet(MutableSet):
        def __init__(self, data=()):
            self._data = set(data)
            self.pop_count = 0
        
        def __contains__(self, item):
            return item in self._data
        
        def __iter__(self):
            return iter(self._data.copy())  # Avoid modification during iteration
        
        def __len__(self):
            return len(self._data)
        
        def add(self, item):
            self._data.add(item)
        
        def discard(self, item):
            self._data.discard(item)
        
        def pop(self):
            self.pop_count += 1
            return super().pop()
    
    ms = TrackingMutableSet([1, 2, 3, 4, 5])
    original_size = len(ms)
    ms.clear()
    
    assert len(ms) == 0
    assert ms.pop_count == original_size


# Test mapping __eq__ with non-Mapping objects
def test_mapping_eq_non_mapping():
    m = MyMapping({'a': 1})
    
    # Comparing with non-Mapping should return NotImplemented
    result = m.__eq__("not a mapping")
    assert result is NotImplemented
    
    # This means Python will try the reverse comparison
    assert m != "not a mapping"


# Check for potential integer overflow in Set._hash
@given(st.lists(st.integers(min_value=0, max_value=2**63-1), max_size=1000))
def test_set_hash_large_values(data):
    s = MySet(data)
    
    # Should not raise OverflowError
    h = s._hash()
    assert isinstance(h, int)
    
    # Should be consistent
    h2 = s._hash()
    assert h == h2


# Test Set inequality operations boundary conditions
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_inequality_boundary(data1, data2):
    s1 = MySet(data1)
    s2 = MySet(data2)
    
    # Check the boundary conditions in __lt__ and __gt__
    # __lt__ requires: len(self) < len(other) AND self <= other
    # __gt__ requires: len(self) > len(other) AND self >= other
    
    if len(s1) < len(s2):
        # s1 < s2 only if s1 is a proper subset
        if s1 <= s2:
            assert s1 < s2
        else:
            assert not (s1 < s2)
    else:
        assert not (s1 < s2)
    
    if len(s1) > len(s2):
        # s1 > s2 only if s1 is a proper superset
        if s1 >= s2:
            assert s1 > s2
        else:
            assert not (s1 > s2)
    else:
        assert not (s1 > s2)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])