import math
from collections.abc import Set, MutableSet, Sequence, MutableSequence, MutableMapping
from hypothesis import given, strategies as st, settings, assume
import pytest


# Concrete implementations for testing
class TestSet(Set):
    def __init__(self, data=()):
        self._data = set(data) if not isinstance(data, set) else data
    
    def __contains__(self, item):
        return item in self._data
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)
    
    def __repr__(self):
        return f"TestSet({self._data})"


class TestMutableSet(MutableSet):
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
    
    def __repr__(self):
        return f"TestMutableSet({self._data})"


class TestMutableSequence(MutableSequence):
    def __init__(self, data=()):
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
    
    def __repr__(self):
        return f"TestMutableSequence({self._data})"


# Property: Set intersection size invariant
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_intersection_size_invariant(data1, data2):
    s1 = TestSet(data1)
    s2 = TestSet(data2)
    intersection = s1 & s2
    
    # Intersection size must be at most the minimum of the two sets
    assert len(intersection) <= min(len(s1), len(s2))
    
    # Every element in intersection must be in both sets
    for elem in intersection:
        assert elem in s1
        assert elem in s2


# Property: Set union commutativity
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_union_commutativity(data1, data2):
    s1 = TestSet(data1)
    s2 = TestSet(data2)
    
    union1 = s1 | s2
    union2 = s2 | s1
    
    # Union should be commutative
    assert set(union1) == set(union2)


# Property: MutableSet __ixor__ with self should clear
@given(st.lists(st.integers()))
def test_mutableset_ixor_self_clears(data):
    ms = TestMutableSet(data)
    original_id = id(ms)
    
    # XOR with self should clear the set
    ms ^= ms
    
    # Should return the same object (in-place operation)
    assert id(ms) == original_id
    
    # Should be empty
    assert len(ms) == 0
    assert list(ms) == []


# Property: MutableSet __ixor__ normal operation
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_mutableset_ixor_normal(data1, data2):
    ms = TestMutableSet(data1)
    s2 = TestMutableSet(data2)
    
    # Store original for comparison
    original_ms = set(ms)
    original_s2 = set(s2)
    
    ms ^= s2
    
    # Result should be symmetric difference
    expected = (original_ms - original_s2) | (original_s2 - original_ms)
    assert set(ms) == expected


# Property: MutableSequence reverse twice gives original
@given(st.lists(st.integers()))
def test_mutablesequence_reverse_idempotent(data):
    seq = TestMutableSequence(data)
    original = list(seq)
    
    seq.reverse()
    seq.reverse()
    
    assert list(seq) == original


# Property: MutableSequence pop and append are inverse
@given(st.lists(st.integers(), min_size=1), st.integers())
def test_mutablesequence_pop_append_inverse(data, value):
    seq = TestMutableSequence(data)
    original_len = len(seq)
    
    seq.append(value)
    assert len(seq) == original_len + 1
    
    popped = seq.pop()
    assert popped == value
    assert len(seq) == original_len


# Property: Set subtraction with itself gives empty set
@given(st.lists(st.integers()))
def test_set_subtraction_self_empty(data):
    s = TestSet(data)
    result = s - s
    assert len(result) == 0
    assert list(result) == []


# Property: Set equality is reflexive
@given(st.lists(st.integers()))
def test_set_equality_reflexive(data):
    s = TestSet(data)
    assert s == s


# Property: Set comparison transitivity
@given(st.lists(st.integers()), st.lists(st.integers()), st.lists(st.integers()))
def test_set_subset_transitivity(data1, data2, data3):
    s1 = TestSet(data1)
    s2 = TestSet(data2)
    s3 = TestSet(data3)
    
    # If s1 <= s2 and s2 <= s3, then s1 <= s3
    if s1 <= s2 and s2 <= s3:
        assert s1 <= s3


# Property: MutableSet clear actually clears
@given(st.lists(st.integers()))
def test_mutableset_clear(data):
    ms = TestMutableSet(data)
    ms.clear()
    assert len(ms) == 0
    assert list(ms) == []


# Property: MutableSet __isub__ with self clears
@given(st.lists(st.integers()))
def test_mutableset_isub_self_clears(data):
    ms = TestMutableSet(data)
    original_id = id(ms)
    
    ms -= ms
    
    # Should return the same object
    assert id(ms) == original_id
    # Should be empty
    assert len(ms) == 0


# Property: Set _hash consistency
@given(st.lists(st.integers(min_value=-100, max_value=100)))
def test_set_hash_consistency(data):
    # Create two sets with the same data
    s1 = TestSet(data)
    s2 = TestSet(data)
    
    # Their hashes should be the same
    h1 = s1._hash()
    h2 = s2._hash()
    assert h1 == h2
    
    # Hash should be deterministic
    h3 = s1._hash()
    assert h1 == h3


# Property: Set isdisjoint correctness
@given(st.lists(st.integers()), st.lists(st.integers()))
def test_set_isdisjoint(data1, data2):
    s1 = TestSet(data1)
    s2 = TestSet(data2)
    
    is_disjoint = s1.isdisjoint(s2)
    
    # Verify by checking intersection
    intersection = s1 & s2
    
    if is_disjoint:
        assert len(intersection) == 0
    else:
        assert len(intersection) > 0


# Test for potential edge case in Set.__xor__
@given(st.lists(st.integers()))
def test_set_xor_self(data):
    s = TestSet(data)
    result = s ^ s
    # XOR with itself should give empty set
    assert len(result) == 0


# Test MutableSequence.extend with self
@given(st.lists(st.integers()))
def test_mutablesequence_extend_self(data):
    seq = TestMutableSequence(data)
    original = list(seq)
    
    seq.extend(seq)
    
    # Should have doubled the sequence
    assert list(seq) == original + original


# Test for sequence index with negative bounds
@given(st.lists(st.integers(), min_size=1))
def test_sequence_index_negative_start(data):
    # Create a basic Sequence implementation
    class TestSequence(Sequence):
        def __init__(self, data):
            self._data = list(data)
        
        def __getitem__(self, index):
            return self._data[index]
        
        def __len__(self):
            return len(self._data)
    
    seq = TestSequence(data)
    value = data[0]  # We know there's at least one element
    
    # Test with negative start
    idx = seq.index(value, start=-len(data))
    assert idx >= 0
    assert seq[idx] == value


# Test MutableMapping setdefault idempotence
class TestMutableMapping(MutableMapping):
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


@given(st.text(), st.integers(), st.integers())
def test_mutablemapping_setdefault_idempotent(key, value1, value2):
    m = TestMutableMapping()
    
    # First setdefault
    result1 = m.setdefault(key, value1)
    assert result1 == value1
    
    # Second setdefault with different value should return the first value
    result2 = m.setdefault(key, value2)
    assert result2 == value1
    assert m[key] == value1


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])