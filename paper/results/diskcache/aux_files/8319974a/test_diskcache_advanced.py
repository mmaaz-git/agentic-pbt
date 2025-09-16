"""Advanced property-based tests for diskcache.persistent module"""

import tempfile
import shutil
import os
from hypothesis import given, strategies as st, assume, settings, note
import hypothesis
import sys
import math

# Add the diskcache environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.persistent import Deque, Index
from diskcache.core import ENOVAL
from collections import OrderedDict


# Strategies
small_lists = st.lists(st.integers(), min_size=0, max_size=20)
tiny_lists = st.lists(st.integers(), min_size=0, max_size=5)
indices = st.integers(min_value=-50, max_value=50)


class TestDequeAdvanced:
    """Advanced tests for Deque edge cases"""
    
    def test_indexing_consistency(self):
        """Indexing should match iteration order"""
        @given(st.lists(st.integers(), min_size=1, max_size=10))
        @settings(max_examples=200)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                
                # Positive indices
                for i in range(len(deque)):
                    from_index = deque[i]
                    from_iter = list(deque)[i]
                    assert from_index == from_iter, f"Index {i}: {from_index} != {from_iter}"
                
                # Negative indices
                for i in range(1, len(deque) + 1):
                    from_index = deque[-i]
                    from_iter = list(deque)[-i]
                    assert from_index == from_iter, f"Index {-i}: {from_index} != {from_iter}"
        
        prop()
    
    def test_maxlen_change_truncates(self):
        """Changing maxlen should truncate from left if needed"""
        @given(
            st.lists(st.integers(), min_size=5, max_size=20),
            st.integers(min_value=1, max_value=4)
        )
        @settings(max_examples=200)
        def prop(items, new_maxlen):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                original_items = list(deque)
                
                # Set smaller maxlen
                deque.maxlen = new_maxlen
                
                # Should keep rightmost items
                assert len(deque) == new_maxlen
                expected = original_items[-new_maxlen:]
                actual = list(deque)
                assert actual == expected, f"Truncation failed: {actual} != {expected}"
        
        prop()
    
    def test_remove_first_occurrence(self):
        """remove() should only remove first occurrence"""
        @given(st.lists(st.integers(min_value=0, max_value=3), min_size=2, max_size=10))
        @settings(max_examples=200)
        def prop(items):
            # Ensure we have duplicates
            if len(set(items)) == len(items):
                return
            
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                
                # Find a value that appears multiple times
                for val in items:
                    if items.count(val) > 1:
                        original_count = deque.count(val)
                        deque.remove(val)
                        new_count = deque.count(val)
                        assert new_count == original_count - 1
                        
                        # Check that first occurrence was removed
                        original_without_first = items.copy()
                        original_without_first.remove(val)
                        assert list(deque) == original_without_first
                        break
        
        prop()
    
    def test_extend_extendleft_order(self):
        """extend adds to right, extendleft adds to left in reverse order"""
        @given(tiny_lists, tiny_lists, tiny_lists)
        @settings(max_examples=200)
        def prop(initial, to_extend, to_extendleft):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(initial, directory=tmpdir)
                
                deque.extend(to_extend)
                deque.extendleft(to_extendleft)
                
                # extendleft adds in reverse order
                expected = list(reversed(to_extendleft)) + initial + to_extend
                actual = list(deque)
                assert actual == expected, f"Extend order wrong: {actual} != {expected}"
        
        prop()
    
    def test_comparison_with_list(self):
        """Deque comparison with list should follow Sequence semantics"""
        @given(small_lists)
        @settings(max_examples=200)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                
                # Equal lists
                assert (deque == items) == True
                assert (deque != items) == False
                
                # Comparison with different list
                if items:
                    different = items[:-1] + [items[-1] + 1]
                    assert (deque == different) == False
                    assert (deque != different) == True
        
        prop()
    
    def test_getitem_setitem_roundtrip(self):
        """Setting and getting items at indices should work correctly"""
        @given(
            st.lists(st.integers(), min_size=1, max_size=10),
            st.integers(),
            st.integers()
        )
        @settings(max_examples=200)
        def prop(items, index, new_value):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                
                # Only test valid indices
                if -len(deque) <= index < len(deque):
                    deque[index] = new_value
                    assert deque[index] == new_value
                    
                    # Check length unchanged
                    assert len(deque) == len(items)
        
        prop()


class TestIndexAdvanced:
    """Advanced tests for Index edge cases"""
    
    def test_pop_with_default(self):
        """pop() with default should return default for missing keys"""
        @given(
            st.dictionaries(st.text(min_size=1), st.integers(), max_size=10),
            st.text(min_size=1),
            st.integers()
        )
        @settings(max_examples=200)
        def prop(items, key, default):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, items)
                
                if key in items:
                    result = index.pop(key, default)
                    assert result == items[key]
                    assert key not in index
                else:
                    result = index.pop(key, default)
                    assert result == default
                    assert len(index) == len(items)
        
        prop()
    
    def test_push_with_prefix(self):
        """push with prefix should create prefixed keys"""
        @given(
            st.lists(st.integers(), min_size=0, max_size=10),
            st.text(min_size=1, max_size=10)
        )
        @settings(max_examples=200)
        def prop(values, prefix):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir)
                
                keys = []
                for val in values:
                    key = index.push(val, prefix=prefix)
                    keys.append(key)
                    assert key.startswith(prefix + '-')
                    assert index[key] == val
                
                # Pull with same prefix should get values in order
                pulled = []
                for _ in range(len(values)):
                    key, val = index.pull(prefix=prefix)
                    pulled.append(val)
                
                assert pulled == values
        
        prop()
    
    def test_peekitem_doesnt_remove(self):
        """peekitem should not remove the item"""
        @given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=1, max_size=10))
        @settings(max_examples=200)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, items)
                original_len = len(index)
                
                # Peek last
                key1, val1 = index.peekitem(last=True)
                assert len(index) == original_len
                assert index[key1] == val1
                
                # Peek first
                key2, val2 = index.peekitem(last=False)
                assert len(index) == original_len
                assert index[key2] == val2
        
        prop()
    
    def test_transact_atomicity(self):
        """Operations in transaction should be atomic"""
        @given(
            st.dictionaries(st.text(min_size=1), st.integers(), max_size=5),
            st.text(min_size=1),
            st.integers()
        )
        @settings(max_examples=100)
        def prop(initial, key, increment):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, initial)
                
                # Atomic increment
                with index.transact():
                    old_val = index.get(key, 0)
                    index[key] = old_val + increment
                
                # Check result
                assert index[key] == initial.get(key, 0) + increment
        
        prop()
    
    def test_keys_values_items_consistency(self):
        """keys(), values(), items() should be consistent with iteration"""
        @given(st.dictionaries(st.text(min_size=1), st.integers(), max_size=10))
        @settings(max_examples=200)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, items)
                
                keys_list = list(index.keys())
                values_list = list(index.values())
                items_list = list(index.items())
                
                # Check consistency
                assert len(keys_list) == len(index)
                assert len(values_list) == len(index)
                assert len(items_list) == len(index)
                
                for i, key in enumerate(keys_list):
                    assert index[key] == values_list[i]
                    assert (key, values_list[i]) == items_list[i]
        
        prop()
    
    def test_reversed_iteration(self):
        """Reversed iteration should give keys in reverse insertion order"""
        @given(st.lists(st.tuples(st.text(min_size=1), st.integers()), min_size=1, max_size=10, unique_by=lambda x: x[0]))
        @settings(max_examples=200)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir)
                
                for k, v in items:
                    index[k] = v
                
                forward_keys = list(index)
                reversed_keys = list(reversed(index))
                
                assert reversed_keys == list(reversed(forward_keys))
        
        prop()


if __name__ == "__main__":
    print("Testing advanced Deque properties...")
    test_deque = TestDequeAdvanced()
    test_deque.test_indexing_consistency()
    test_deque.test_maxlen_change_truncates()
    test_deque.test_remove_first_occurrence()
    test_deque.test_extend_extendleft_order()
    test_deque.test_comparison_with_list()
    test_deque.test_getitem_setitem_roundtrip()
    
    print("Testing advanced Index properties...")
    test_index = TestIndexAdvanced()
    test_index.test_pop_with_default()
    test_index.test_push_with_prefix()
    test_index.test_peekitem_doesnt_remove()
    test_index.test_transact_atomicity()
    test_index.test_keys_values_items_consistency()
    test_index.test_reversed_iteration()
    
    print("All advanced tests completed!")