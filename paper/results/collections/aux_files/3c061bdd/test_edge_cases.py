import sys
import math
from collections.abc import Set, MutableSet, Sequence, MutableSequence, Mapping, MutableMapping
from hypothesis import given, strategies as st, settings, assume
import pytest


# Let's look for actual bugs in edge cases

class MySet(Set):
    def __init__(self, data=()):
        self._data = set(data) if not isinstance(data, set) else data
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)


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


# Test MutableMapping.pop with default=None specifically
def test_mutablemapping_pop_none_default():
    m = MyMapping({'key': 'value'})
    
    # Pop with None as default
    result = m.pop('missing_key', None)
    assert result is None
    
    # Pop existing key
    result = m.pop('key', None)
    assert result == 'value'
    
    # Key should be gone
    assert 'key' not in m


# Test Sequence operations with specific slicing edge cases
class MySequence(Sequence):
    def __init__(self, data):
        self._data = list(data)
    
    def __getitem__(self, index):
        return self._data[index]
    
    def __len__(self):
        return len(self._data)


@given(st.lists(st.integers(), min_size=1))
def test_sequence_index_start_equals_length(data):
    seq = MySequence(data)
    value = data[0]
    
    # When start == len(seq), should not find anything
    with pytest.raises(ValueError):
        seq.index(value, start=len(seq))


# Test MutableMapping popitem behavior more thoroughly
def test_mutablemapping_popitem_implementation():
    # The popitem implementation uses next(iter(self))
    # Let's test if this works correctly with a custom iterator
    
    class CustomIterMapping(MutableMapping):
        def __init__(self):
            self._data = {}
            self.iter_count = 0
        
        def __getitem__(self, key):
            return self._data[key]
        
        def __setitem__(self, key, value):
            self._data[key] = value
        
        def __delitem__(self, key):
            del self._data[key]
        
        def __iter__(self):
            self.iter_count += 1
            return iter(self._data)
        
        def __len__(self):
            return len(self._data)
    
    m = CustomIterMapping()
    m['a'] = 1
    m['b'] = 2
    
    key, value = m.popitem()
    assert key in ['a', 'b']
    assert m.iter_count == 1
    assert len(m) == 1


# Test Set operations when comparing with NotImplemented returns
class NonComparableSet(Set):
    def __init__(self, data=()):
        self._data = set(data)
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)
    
    def __le__(self, other):
        # Always return NotImplemented for testing
        return NotImplemented


def test_set_comparison_notimplemented():
    s1 = NonComparableSet([1, 2, 3])
    s2 = NonComparableSet([1, 2])
    
    # Since __le__ returns NotImplemented, comparison should fall back 
    # This tests if the ABCs handle NotImplemented correctly
    # The comparison will ultimately fail
    try:
        result = s1 <= s2
        # If we get here, Python tried reverse comparison
        assert result is NotImplemented or result is False
    except TypeError:
        # Expected if neither comparison works
        pass


# Test MutableSequence operations with negative indices
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


@given(st.lists(st.integers(), min_size=2))
def test_mutablesequence_pop_negative_index(data):
    seq = MyMutableSeq(data)
    
    # Pop with -1 (last element)
    last = seq[-1]
    popped = seq.pop(-1)
    assert popped == last
    assert len(seq) == len(data) - 1


# Test interesting case with MutableSet operations
class IterModifyingSet(MutableSet):
    """A set that modifies during iteration - testing undefined behavior"""
    def __init__(self, data=()):
        self._data = set(data)
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        # This is intentionally bad - modifying during iteration
        for item in list(self._data):
            yield item
    
    def __len__(self):
        return len(self._data)
    
    def add(self, item):
        self._data.add(item)
    
    def discard(self, item):
        self._data.discard(item)


# Test Mapping.get with unusual defaults
@given(st.text(), st.one_of(st.none(), st.integers(), st.text()))
def test_mapping_get_various_defaults(key, default):
    m = MyMapping()
    
    # get should return the default for missing keys
    result = m.get(key, default)
    assert result is default
    
    # Add the key
    m[key] = "value"
    result = m.get(key, default)
    assert result == "value"


# Test Set hash with hash collisions
def test_set_hash_collision_handling():
    # Create objects with known hash collisions
    class HashCollider:
        def __init__(self, value, hash_val):
            self.value = value
            self._hash = hash_val
        
        def __hash__(self):
            return self._hash
        
        def __eq__(self, other):
            if not isinstance(other, HashCollider):
                return False
            return self.value == other.value
    
    # These will have the same hash but different values
    obj1 = HashCollider("a", 42)
    obj2 = HashCollider("b", 42)
    
    s1 = MySet([obj1])
    s2 = MySet([obj2])
    s3 = MySet([obj1, obj2])
    
    # Even with hash collisions, the set hash should handle them
    h1 = s1._hash()
    h2 = s2._hash()
    h3 = s3._hash()
    
    # Different sets should (likely) have different hashes
    # Can't guarantee this due to hash collisions, but the algorithm should try
    assert isinstance(h1, int)
    assert isinstance(h2, int)
    assert isinstance(h3, int)


# Test MutableMapping update with self
def test_mutablemapping_update_self():
    m = MyMapping({'a': 1, 'b': 2})
    
    # Update with itself - should work
    m.update(m)
    
    assert m == {'a': 1, 'b': 2}
    
    # Update with self and kwargs
    m.update(m, c=3)
    assert m == {'a': 1, 'b': 2, 'c': 3}


# Look for issues with Sequence.count and index with identity vs equality
class IdentitySequence(Sequence):
    def __init__(self, data):
        self._data = list(data)
    
    def __getitem__(self, index):
        return self._data[index]
    
    def __len__(self):
        return len(self._data)


def test_sequence_identity_vs_equality():
    # The implementation uses "v is value or v == value"
    # Let's test with objects where identity matters
    
    class IdentityObject:
        def __init__(self, value):
            self.value = value
        
        def __eq__(self, other):
            # Always returns False for testing
            return False
    
    obj1 = IdentityObject(1)
    obj2 = IdentityObject(1)
    
    seq = IdentitySequence([obj1, obj2, obj1])
    
    # Count should find obj1 twice (using 'is')
    count = seq.count(obj1)
    assert count == 2
    
    # But obj2 appears once
    count = seq.count(obj2)
    assert count == 1
    
    # A new object with same value shouldn't be found (eq returns False)
    obj3 = IdentityObject(1)
    count = seq.count(obj3)
    assert count == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])