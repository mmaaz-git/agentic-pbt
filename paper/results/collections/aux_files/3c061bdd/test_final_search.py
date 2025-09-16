import sys
import gc
from collections.abc import Set, MutableSet, MutableMapping, MutableSequence, Mapping
from hypothesis import given, strategies as st, settings, assume
import pytest


# Final search for genuine bugs

class TestSet(Set):
    def __init__(self, data=()):
        self._data = set(data)
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)


# Test for potential issue in Set.__ge__ and __le__ short-circuit logic
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_comparison_shortcircuit(data1, data2):
    s1 = TestSet(data1)
    s2 = TestSet(data2)
    
    # The implementation short-circuits based on length
    # Let's verify this is correct
    
    # For <=: if len(self) > len(other), returns False immediately
    if len(s1) > len(s2):
        result = s1 <= s2
        # This should be False since a larger set can't be subset of smaller
        assert result is False
        
        # Verify this is correct
        for elem in s1:
            if elem not in s2:
                break
        else:
            # If we get here, all elements of s1 are in s2, but s1 is larger
            # This would be impossible
            assert False, "Larger set cannot be subset"
    
    # For >=: if len(self) < len(other), returns False immediately  
    if len(s1) < len(s2):
        result = s1 >= s2
        assert result is False
        
        # Verify correctness
        for elem in s2:
            if elem not in s1:
                break
        else:
            # If all elements of s2 are in s1, but s1 is smaller
            # This would be impossible
            assert False, "Smaller set cannot be superset"


# Test MutableMapping with __marker sentinel
def test_mutablemapping_pop_marker():
    """Test that the __marker sentinel works correctly"""
    
    class MarkerTestMapping(MutableMapping):
        def __init__(self):
            self._data = {}
        
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
    
    m = MarkerTestMapping()
    
    # The __marker is used to distinguish "no default" from "default is None"
    # When no default is provided, KeyError should be raised
    with pytest.raises(KeyError):
        m.pop('missing_key')
    
    # With None as default, should return None
    result = m.pop('missing_key', None)
    assert result is None
    
    # With any other default, should return that default
    result = m.pop('missing_key', 'default')
    assert result == 'default'


# Test potential issue with MutableSequence.reverse index calculation
class TestMutableSeq(MutableSequence):
    def __init__(self, data):
        self._data = list(data)
        self.access_pattern = []
    
    def __getitem__(self, index):
        self.access_pattern.append(('get', index))
        return self._data[index]
    
    def __setitem__(self, index, value):
        self.access_pattern.append(('set', index, value))
        self._data[index] = value
    
    def __delitem__(self, index):
        del self._data[index]
    
    def __len__(self):
        return len(self._data)
    
    def insert(self, index, value):
        self._data.insert(index, value)


@given(st.lists(st.integers(), min_size=2, max_size=10))
def test_mutablesequence_reverse_access_pattern(data):
    seq = TestMutableSeq(data)
    seq.reverse()
    
    # Check the access pattern
    n = len(data)
    expected_swaps = n // 2
    
    # Count actual swaps
    set_ops = [op for op in seq.access_pattern if op[0] == 'set']
    
    # Each swap involves 2 sets (except the swap is done with parallel assignment)
    # Actually in the implementation: self[i], self[n-i-1] = self[n-i-1], self[i]
    # This should result in 2 gets and 2 sets per swap
    
    # Verify the result is correct
    assert list(seq) == list(reversed(data))


# Test edge case in Set operations with empty sets
def test_set_operations_empty():
    empty = TestSet([])
    s = TestSet([1, 2, 3])
    
    # Operations with empty set
    assert len(empty & s) == 0
    assert set(empty | s) == {1, 2, 3}
    assert set(s - empty) == {1, 2, 3}
    assert set(empty - s) == set()
    assert set(empty ^ s) == {1, 2, 3}
    
    # Comparisons with empty
    assert empty <= s
    assert empty < s
    assert not (empty >= s)
    assert not (empty > s)
    assert not (empty == s)
    
    # Empty with empty
    assert empty <= empty
    assert empty >= empty
    assert empty == empty
    assert not (empty < empty)
    assert not (empty > empty)


# Test MutableMapping setdefault edge case
def test_mutablemapping_setdefault_exception():
    """Test setdefault when __setitem__ raises an exception"""
    
    class FailingMapping(MutableMapping):
        def __init__(self):
            self._data = {}
            self.fail_next_set = False
        
        def __getitem__(self, key):
            return self._data[key]
        
        def __setitem__(self, key, value):
            if self.fail_next_set:
                self.fail_next_set = False
                raise ValueError("Simulated failure")
            self._data[key] = value
        
        def __delitem__(self, key):
            del self._data[key]
        
        def __iter__(self):
            return iter(self._data)
        
        def __len__(self):
            return len(self._data)
    
    m = FailingMapping()
    
    # Normal setdefault
    result = m.setdefault('key1', 'value1')
    assert result == 'value1'
    assert m['key1'] == 'value1'
    
    # setdefault when set fails
    m.fail_next_set = True
    with pytest.raises(ValueError):
        m.setdefault('key2', 'value2')
    
    # key2 should not be in the mapping
    assert 'key2' not in m


# Test for consistency in Set._from_iterable
@given(st.lists(st.integers()))
def test_set_from_iterable_consistency(data):
    s = TestSet(data)
    
    # _from_iterable should create a new instance of the same type
    s2 = s._from_iterable(data)
    
    assert type(s2) == type(s)
    assert set(s2) == set(data)


# Look for issues with large hash values
def test_set_hash_boundary_values():
    """Test hash with boundary values"""
    
    # Test with maxsize
    s1 = TestSet([sys.maxsize])
    h1 = s1._hash()
    assert isinstance(h1, int)
    
    # Test with -maxsize
    s2 = TestSet([-sys.maxsize])
    h2 = s2._hash()
    assert isinstance(h2, int)
    
    # Test with multiple maxsize values
    s3 = TestSet([sys.maxsize, sys.maxsize - 1, -sys.maxsize])
    h3 = s3._hash()
    assert isinstance(h3, int)


# Test MutableSet operations preserve type
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_mutableset_operations_preserve_type(data1, data2):
    class CustomMutableSet(MutableSet):
        def __init__(self, data=()):
            self._data = set(data)
            self.custom_attr = "custom"
        
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
    
    ms1 = CustomMutableSet(data1)
    ms2 = CustomMutableSet(data2)
    
    # Regular operations should return new instances, not modify in place
    result = ms1 & ms2
    assert type(result) == CustomMutableSet
    
    result = ms1 | ms2
    assert type(result) == CustomMutableSet
    
    result = ms1 - ms2
    assert type(result) == CustomMutableSet
    
    result = ms1 ^ ms2
    assert type(result) == CustomMutableSet


# Test Mapping contains with exceptions
def test_mapping_contains_exception():
    """Test __contains__ when __getitem__ raises unexpected exception"""
    
    class ExceptionMapping(Mapping):
        def __init__(self):
            self._data = {'exists': 1}
        
        def __getitem__(self, key):
            if key == 'error':
                raise ValueError("Unexpected error")
            return self._data[key]
        
        def __iter__(self):
            return iter(self._data)
        
        def __len__(self):
            return len(self._data)
    
    m = ExceptionMapping()
    
    # Normal contains
    assert 'exists' in m
    assert 'missing' not in m
    
    # Contains with exception - should propagate
    with pytest.raises(ValueError):
        'error' in m


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])