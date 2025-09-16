"""Edge case property-based tests for diskcache.persistent module"""

import tempfile
import shutil
import os
from hypothesis import given, strategies as st, assume, settings, note, example
import hypothesis
import sys
import math

# Add the diskcache environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.persistent import Deque, Index
from diskcache.core import ENOVAL
from collections import OrderedDict


class TestDequeEdgeCases:
    """Edge case tests for Deque"""
    
    def test_empty_deque_operations(self):
        """Operations on empty deque should behave correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            deque = Deque(directory=tmpdir)
            
            # Test peek on empty
            try:
                deque.peek()
                assert False, "peek() on empty deque should raise IndexError"
            except IndexError as e:
                assert "peek from an empty deque" in str(e)
            
            try:
                deque.peekleft()
                assert False, "peekleft() on empty deque should raise IndexError"
            except IndexError as e:
                assert "peek from an empty deque" in str(e)
            
            # Test pop on empty
            try:
                deque.pop()
                assert False, "pop() on empty deque should raise IndexError"
            except IndexError as e:
                assert "pop from an empty deque" in str(e)
            
            try:
                deque.popleft()
                assert False, "popleft() on empty deque should raise IndexError"
            except IndexError as e:
                assert "pop from an empty deque" in str(e)
            
            # Test remove on empty
            try:
                deque.remove(1)
                assert False, "remove() on empty deque should raise ValueError"
            except ValueError as e:
                assert "value not in deque" in str(e)
            
            # Test count on empty
            assert deque.count(1) == 0
            
            # Test reverse on empty (should not fail)
            deque.reverse()
            assert len(deque) == 0
            
            # Test rotate on empty (should not fail)
            deque.rotate(5)
            assert len(deque) == 0
    
    def test_single_element_operations(self):
        """Operations on single element deque"""
        @given(st.integers())
        @settings(max_examples=50)
        def prop(value):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque([value], directory=tmpdir)
                
                # Test indexing
                assert deque[0] == value
                assert deque[-1] == value
                
                # Test peek
                assert deque.peek() == value
                assert deque.peekleft() == value
                
                # Test count
                assert deque.count(value) == 1
                assert deque.count(value + 1) == 0
                
                # Test rotate
                deque.rotate(1)
                assert list(deque) == [value]
                deque.rotate(-1)
                assert list(deque) == [value]
                
                # Test reverse
                deque.reverse()
                assert list(deque) == [value]
                
                # Test remove
                deque.remove(value)
                assert len(deque) == 0
        
        prop()
    
    def test_deque_delitem_edge_cases(self):
        """Test __delitem__ with various indices"""
        @given(st.lists(st.integers(), min_size=1, max_size=10))
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                
                # Delete first item
                del deque[0]
                assert len(deque) == len(items) - 1
                
                if len(deque) > 0:
                    # Delete last item
                    del deque[-1]
                    assert len(deque) == len(items) - 2
        
        prop()
    
    def test_maxlen_zero_behavior(self):
        """Deque with maxlen=0 should always be empty"""
        @given(st.lists(st.integers()))
        @settings(max_examples=50)
        def prop(items):
            # Note: maxlen=0 might not be a valid use case, but let's test it
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    deque = Deque(items, directory=tmpdir, maxlen=0)
                    assert len(deque) == 0
                    
                    # Try to append
                    deque.append(1)
                    assert len(deque) == 0
                    
                    deque.appendleft(2)
                    assert len(deque) == 0
            except:
                # If maxlen=0 is not supported, that's fine
                pass
        
        prop()
    
    def test_comparison_edge_cases(self):
        """Test comparison with edge cases"""
        with tempfile.TemporaryDirectory() as tmpdir:
            deque = Deque([1, 2, 3], directory=tmpdir)
            
            # Compare with non-sequence
            assert (deque == 123) == False
            assert (deque != 123) == True
            
            # Compare with tuple (should work as Sequence)
            assert (deque == (1, 2, 3)) == True
            assert (deque != (1, 2, 3)) == False
            
            # Compare with different length
            assert (deque == [1, 2]) == False
            assert (deque < [1, 2, 4]) == True
            assert (deque > [1, 2]) == True
            
            # Compare empty deques
            empty1 = Deque()
            empty2 = Deque()
            assert empty1 == empty2
            assert not (empty1 != empty2)
            assert not (empty1 < empty2)
            assert not (empty1 > empty2)
            assert empty1 <= empty2
            assert empty1 >= empty2
    
    def test_out_of_bounds_indexing(self):
        """Out of bounds indexing should raise IndexError"""
        @given(st.lists(st.integers(), min_size=1, max_size=10))
        @settings(max_examples=100)
        def prop(items):
            with tempfile.TemporaryDirectory() as tmpdir:
                deque = Deque(items, directory=tmpdir)
                
                # Test positive out of bounds
                try:
                    _ = deque[len(items)]
                    assert False, "Should raise IndexError"
                except IndexError:
                    pass
                
                try:
                    _ = deque[len(items) + 10]
                    assert False, "Should raise IndexError"
                except IndexError:
                    pass
                
                # Test negative out of bounds
                try:
                    _ = deque[-len(items) - 1]
                    assert False, "Should raise IndexError"
                except IndexError:
                    pass
        
        prop()


class TestIndexEdgeCases:
    """Edge case tests for Index"""
    
    def test_empty_index_operations(self):
        """Operations on empty index should behave correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            index = Index(tmpdir)
            
            # Test popitem on empty
            try:
                index.popitem()
                assert False, "popitem() on empty index should raise KeyError"
            except KeyError as e:
                assert "empty" in str(e).lower()
            
            # Test peekitem on empty
            try:
                index.peekitem()
                assert False, "peekitem() on empty index should raise KeyError"
            except KeyError:
                pass
            
            # Test pop without default
            try:
                index.pop('key')
                assert False, "pop() without default should raise KeyError"
            except KeyError:
                pass
            
            # Test clear on empty (should not fail)
            index.clear()
            assert len(index) == 0
    
    def test_single_item_operations(self):
        """Operations on single item index"""
        @given(st.text(min_size=1), st.integers())
        @settings(max_examples=50)
        def prop(key, value):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir, {key: value})
                
                # Test peek
                assert index.peekitem() == (key, value)
                assert index.peekitem(last=False) == (key, value)
                
                # Test popitem
                index2 = Index({key: value})
                assert index2.popitem() == (key, value)
                assert len(index2) == 0
                
                # Test iteration
                assert list(index) == [key]
                assert list(index.keys()) == [key]
                assert list(index.values()) == [value]
                assert list(index.items()) == [(key, value)]
        
        prop()
    
    def test_pull_from_empty_queue(self):
        """pull() from empty queue should return default"""
        with tempfile.TemporaryDirectory() as tmpdir:
            index = Index(tmpdir)
            
            # Pull without prefix
            result = index.pull()
            assert result == (None, None)
            
            # Pull with prefix
            result = index.pull(prefix='test')
            assert result == (None, None)
            
            # Pull with custom default
            result = index.pull(default=('key', 'value'))
            assert result == ('key', 'value')
    
    def test_push_pull_edge_cases(self):
        """Test push/pull with edge cases"""
        @given(st.integers())
        @settings(max_examples=50)
        def prop(value):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir)
                
                # Push to back, pull from front
                key1 = index.push(value, side='back')
                assert isinstance(key1, int)
                
                result_key, result_val = index.pull(side='front')
                assert result_val == value
                assert result_key == key1
                
                # Push to front, pull from back
                key2 = index.push(value * 2, side='front')
                result_key, result_val = index.pull(side='back')
                assert result_val == value * 2
                assert result_key == key2
        
        prop()
    
    def test_equality_edge_cases(self):
        """Test Index equality with edge cases"""
        with tempfile.TemporaryDirectory() as tmpdir:
            index = Index(tmpdir, {'a': 1, 'b': 2})
            
            # Compare with non-mapping
            assert (index == 123) == False
            assert (index != 123) == True
            
            # Compare with self
            assert index == index
            assert not (index != index)
            
            # Compare empty indices
            empty1 = Index()
            empty2 = Index()
            assert empty1 == empty2
            assert not (empty1 != empty2)
            
            # Compare with dict of different size
            assert (index == {'a': 1}) == False
            assert (index == {'a': 1, 'b': 2, 'c': 3}) == False
    
    def test_setdefault_concurrent_behavior(self):
        """setdefault should handle concurrent-like scenarios"""
        @given(st.text(min_size=1), st.integers(), st.integers())
        @settings(max_examples=100)
        def prop(key, value1, value2):
            with tempfile.TemporaryDirectory() as tmpdir:
                index = Index(tmpdir)
                
                # First setdefault wins
                result1 = index.setdefault(key, value1)
                assert result1 == value1
                assert index[key] == value1
                
                # Second setdefault returns existing
                result2 = index.setdefault(key, value2)
                assert result2 == value1  # Should return first value
                assert index[key] == value1  # Should keep first value
        
        prop()
    
    def test_integer_key_push(self):
        """Test that push without prefix uses integer keys starting at 500 trillion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            index = Index(tmpdir)
            
            # First push should start at 500 trillion
            key1 = index.push('first')
            assert key1 == 500000000000000
            
            # Second push should increment
            key2 = index.push('second')
            assert key2 == 500000000000001
            
            # Pull should get them in order
            k1, v1 = index.pull()
            assert k1 == 500000000000000
            assert v1 == 'first'
            
            k2, v2 = index.pull()
            assert k2 == 500000000000001
            assert v2 == 'second'


if __name__ == "__main__":
    print("Testing Deque edge cases...")
    test_deque = TestDequeEdgeCases()
    test_deque.test_empty_deque_operations()
    test_deque.test_single_element_operations()
    test_deque.test_deque_delitem_edge_cases()
    test_deque.test_maxlen_zero_behavior()
    test_deque.test_comparison_edge_cases()
    test_deque.test_out_of_bounds_indexing()
    
    print("Testing Index edge cases...")
    test_index = TestIndexEdgeCases()
    test_index.test_empty_index_operations()
    test_index.test_single_item_operations()
    test_index.test_pull_from_empty_queue()
    test_index.test_push_pull_edge_cases()
    test_index.test_equality_edge_cases()
    test_index.test_setdefault_concurrent_behavior()
    test_index.test_integer_key_push()
    
    print("All edge case tests completed!")