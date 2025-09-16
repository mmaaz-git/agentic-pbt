"""Property-based tests for diskcache.persistent module"""

import tempfile
import shutil
import os
from hypothesis import given, strategies as st, assume, settings
import hypothesis
import sys
import math

# Add the diskcache environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.persistent import Deque, Index
from collections import OrderedDict


# Strategy for generating small sequences to avoid memory/performance issues
small_lists = st.lists(st.integers(), min_size=0, max_size=20)
tiny_lists = st.lists(st.integers(), min_size=0, max_size=10)

# Strategy for reasonable maxlen values
reasonable_maxlen = st.integers(min_value=1, max_value=100)

# Strategy for rotation steps
rotation_steps = st.integers(min_value=-50, max_value=50)


class TestDeque:
    """Test properties of the Deque class"""
    
    def test_reverse_idempotence(self):
        """Reversing twice should restore original order"""
        @given(small_lists)
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                original = list(deque)
                
                deque.reverse()
                deque.reverse()
                
                result = list(deque)
                assert result == original, f"Double reverse failed: {original} != {result}"
        
        prop()
    
    def test_rotation_round_trip(self):
        """rotate(n) followed by rotate(-n) should restore original"""
        @given(small_lists, rotation_steps)
        @settings(max_examples=100)
        def prop(items, steps):
            if not items:  # Skip empty deques
                return
                
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                original = list(deque)
                
                deque.rotate(steps)
                deque.rotate(-steps)
                
                result = list(deque)
                assert result == original, f"Rotation round-trip failed: {original} != {result}"
        
        prop()
    
    def test_maxlen_enforcement(self):
        """Deque should never exceed maxlen when set"""
        @given(small_lists, reasonable_maxlen)
        @settings(max_examples=100)
        def prop(items, maxlen):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(maxlen=maxlen, directory=tmpdir)
                
                # Add items one by one and check length constraint
                for item in items:
                    deque.append(item)
                    assert len(deque) <= maxlen, f"Deque exceeded maxlen: {len(deque)} > {maxlen}"
                
                # Final check
                assert len(deque) == min(len(items), maxlen)
        
        prop()
    
    def test_equality_reflexive(self):
        """Deque should equal itself"""
        @given(small_lists)
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                assert deque == deque, "Deque not equal to itself"
                assert not (deque != deque), "Deque not-equal to itself"
        
        prop()
    
    def test_append_pop_inverse(self):
        """append followed by pop should return the appended value"""
        @given(small_lists, st.integers())
        @settings(max_examples=100)
        def prop(initial_items, value):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(initial_items, directory=tmpdir)
                initial_len = len(deque)
                
                deque.append(value)
                assert len(deque) == initial_len + 1
                
                popped = deque.pop()
                assert popped == value
                assert len(deque) == initial_len
        
        prop()
    
    def test_appendleft_popleft_inverse(self):
        """appendleft followed by popleft should return the appended value"""
        @given(small_lists, st.integers())
        @settings(max_examples=100)
        def prop(initial_items, value):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(initial_items, directory=tmpdir)
                initial_len = len(deque)
                
                deque.appendleft(value)
                assert len(deque) == initial_len + 1
                
                popped = deque.popleft()
                assert popped == value
                assert len(deque) == initial_len
        
        prop()
    
    def test_count_consistency(self):
        """count(x) should equal the number of x's when iterating"""
        @given(st.lists(st.integers(min_value=0, max_value=5), min_size=0, max_size=20))
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                
                for value in set(items):
                    count_method = deque.count(value)
                    count_manual = sum(1 for x in deque if x == value)
                    assert count_method == count_manual, f"Count mismatch for {value}: {count_method} != {count_manual}"
        
        prop()


class TestIndex:
    """Test properties of the Index class"""
    
    def test_length_invariant(self):
        """len(index) should equal len(list(index.keys()))"""
        @given(st.dictionaries(st.text(min_size=1), st.integers(), max_size=20))
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir)
                index.update(items)
                
                len_index = len(index)
                len_keys = len(list(index.keys()))
                assert len_index == len_keys, f"Length mismatch: {len_index} != {len_keys}"
        
        prop()
    
    def test_setdefault_property(self):
        """setdefault should return existing value or set and return default"""
        @given(
            st.dictionaries(st.text(min_size=1), st.integers(), max_size=10),
            st.text(min_size=1),
            st.integers()
        )
        @settings(max_examples=100)
        def prop(initial_items, key, default):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, initial_items)
                
                if key in initial_items:
                    # Key exists - should return existing value
                    result = index.setdefault(key, default)
                    assert result == initial_items[key]
                    assert index[key] == initial_items[key]
                else:
                    # Key doesn't exist - should set and return default
                    result = index.setdefault(key, default)
                    assert result == default
                    assert index[key] == default
        
        prop()
    
    def test_popitem_ordering(self):
        """popitem(last=True) should pop last inserted, last=False should pop first"""
        @given(st.lists(st.tuples(st.text(min_size=1), st.integers()), min_size=1, max_size=10, unique_by=lambda x: x[0]))
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Test last=True (LIFO)
                index1 = Index(tmpdir)
                for k, v in items:
                    index1[k] = v
                
                popped_key, popped_val = index1.popitem(last=True)
                assert popped_key == items[-1][0]
                assert popped_val == items[-1][1]
                
                # Test last=False (FIFO) with fresh index
                with tempfile.TemporaryDirectory() as tmpdir2:
                    index2 = Index(tmpdir2)
                    for k, v in items:
                        index2[k] = v
                    
                    popped_key, popped_val = index2.popitem(last=False)
                    assert popped_key == items[0][0]
                    assert popped_val == items[0][1]
        
        prop()
    
    def test_push_pull_fifo(self):
        """push/pull with side='front' should maintain FIFO semantics"""
        @given(st.lists(st.integers(), min_size=0, max_size=20))
        @settings(max_examples=100)
        def prop(values):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir)
                
                # Push all values
                keys = []
                for val in values:
                    key = index.push(val)
                    keys.append(key)
                
                # Pull all values (FIFO)
                pulled_values = []
                for _ in range(len(values)):
                    key, val = index.pull()
                    pulled_values.append(val)
                
                assert pulled_values == values, f"FIFO violation: {values} != {pulled_values}"
        
        prop()
    
    def test_equality_with_dict(self):
        """Index with same key-value pairs should equal a dict (order-insensitive)"""
        @given(st.dictionaries(st.text(min_size=1), st.integers(), max_size=10))
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, items)
                assert index == items, "Index not equal to dict with same items"
                
                # Also test with OrderedDict (order-sensitive)
                od = OrderedDict(items)
                index2 = Index()
                for k, v in od.items():
                    index2[k] = v
                assert index2 == od
        
        prop()
    
    def test_clear_empties_index(self):
        """clear() should remove all items"""
        @given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=1, max_size=10))
        @settings(max_examples=100) 
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, items)
                assert len(index) > 0
                
                index.clear()
                assert len(index) == 0
                assert list(index) == []
                assert dict(index) == {}
        
        prop()


if __name__ == "__main__":
    print("Testing Deque properties...")
    test_deque = TestDeque()
    test_deque.test_reverse_idempotence()
    test_deque.test_rotation_round_trip()
    test_deque.test_maxlen_enforcement()
    test_deque.test_equality_reflexive()
    test_deque.test_append_pop_inverse()
    test_deque.test_appendleft_popleft_inverse()
    test_deque.test_count_consistency()
    
    print("Testing Index properties...")
    test_index = TestIndex()
    test_index.test_length_invariant()
    test_index.test_setdefault_property()
    test_index.test_popitem_ordering()
    test_index.test_push_pull_fifo()
    test_index.test_equality_with_dict()
    test_index.test_clear_empties_index()
    
    print("All tests completed!")