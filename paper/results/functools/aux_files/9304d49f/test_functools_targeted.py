"""Targeted property tests looking for specific edge cases in functools"""
import functools
import operator
from hypothesis import given, strategies as st, assume, settings, example
import gc
import sys


# Test 1: lru_cache with hash collisions
def test_lru_cache_hash_collision():
    """lru_cache should handle hash collisions correctly"""
    
    class BadHash:
        def __init__(self, value):
            self.value = value
        
        def __hash__(self):
            return 1  # All instances have same hash!
        
        def __eq__(self, other):
            return isinstance(other, BadHash) and self.value == other.value
    
    call_count = 0
    
    @functools.lru_cache(maxsize=128)
    def process(obj):
        nonlocal call_count
        call_count += 1
        return obj.value
    
    # Different objects with same hash
    obj1 = BadHash(1)
    obj2 = BadHash(2)
    obj3 = BadHash(1)  # Equal to obj1
    
    result1 = process(obj1)
    assert result1 == 1
    assert call_count == 1
    
    result2 = process(obj2)
    assert result2 == 2
    assert call_count == 2  # Different object, should not hit cache
    
    result3 = process(obj3)
    assert result3 == 1
    assert call_count == 2  # Equal to obj1, should hit cache


# Test 2: partial with method references and garbage collection
def test_partial_method_gc():
    """partial should not prevent garbage collection of objects"""
    
    class MyClass:
        def method(self, x):
            return x * 2
    
    obj = MyClass()
    weak_ref = weakref.ref(obj)
    
    # Create partial with bound method
    p = functools.partial(obj.method)
    
    # This keeps a reference to obj through the bound method
    assert weak_ref() is not None
    
    # Delete the partial
    del p
    del obj
    gc.collect()
    
    # Object should be collected
    assert weak_ref() is None


# Test 3: singledispatch with None type registration
def test_singledispatch_none_type():
    """singledispatch should handle None type correctly"""
    
    @functools.singledispatch
    def process(arg):
        return f"default: {type(arg).__name__}"
    
    @process.register(type(None))
    def _(arg):
        return "None type"
    
    @process.register(int)
    def _(arg):
        return f"int: {arg}"
    
    assert process(None) == "None type"
    assert process(0) == "int: 0"
    assert process(False) == "int: False"  # bool is subclass of int


# Test 4: Complex interaction between partial and pickle
@given(st.integers(), st.integers())
def test_partial_pickle_complex(a, b):
    """Test complex pickling scenarios with partial"""
    import pickle
    
    # Global function that can be pickled
    partial_func = functools.partial(operator.add, a)
    
    # Test pickling
    pickled = pickle.dumps(partial_func)
    unpickled = pickle.loads(pickled)
    
    assert unpickled(b) == a + b
    
    # Test nested partial pickling
    nested = functools.partial(partial_func, b)
    pickled2 = pickle.dumps(nested)
    unpickled2 = pickle.loads(pickled2)
    
    assert unpickled2() == a + b


# Test 5: reduce with modifying iterator
def test_reduce_modifying_iterator():
    """reduce with iterator that modifies external state"""
    
    external_list = []
    
    class ModifyingIterator:
        def __iter__(self):
            for i in range(3):
                external_list.append(i)
                yield i
    
    result = functools.reduce(operator.add, ModifyingIterator(), 0)
    
    assert result == 0 + 1 + 2
    assert external_list == [0, 1, 2]


# Test 6: lru_cache with maxsize=None (unbounded)
@given(st.lists(st.integers(), min_size=100, max_size=200))
def test_lru_cache_unbounded(values):
    """lru_cache with maxsize=None should cache everything"""
    
    call_count = 0
    
    @functools.lru_cache(maxsize=None)
    def identity(x):
        nonlocal call_count
        call_count += 1
        return x
    
    # First pass - all misses
    for v in values:
        identity(v)
    
    first_count = call_count
    
    # Second pass - all should be cached
    for v in values:
        identity(v)
    
    # Count should not increase if all were cached
    unique_values = len(set(values))
    assert call_count == unique_values


# Test 7: total_ordering with equal objects
@given(st.integers())
def test_total_ordering_equality_consistency(x):
    """total_ordering should maintain consistency with equality"""
    
    @functools.total_ordering
    class Number:
        def __init__(self, value):
            self.value = value
        
        def __eq__(self, other):
            if not isinstance(other, Number):
                return NotImplemented
            return self.value == other.value
        
        def __lt__(self, other):
            if not isinstance(other, Number):
                return NotImplemented
            return self.value < other.value
    
    a = Number(x)
    b = Number(x)  # Equal value
    
    # Equal objects should satisfy these properties
    assert a == b
    assert not (a < b)
    assert not (a > b)
    assert a <= b
    assert a >= b
    
    # Reflexivity
    assert a == a
    assert a <= a
    assert a >= a


# Test 8: cmp_to_key with NaN-like behavior
def test_cmp_to_key_nan_behavior():
    """Test cmp_to_key with comparison that returns inconsistent results"""
    
    def nan_cmp(a, b):
        # Simulate NaN-like behavior: not equal to anything including itself
        if a == "nan" or b == "nan":
            if a == b:
                return 0  # But equal for same reference
            return -1 if a == "nan" else 1
        return (a > b) - (a < b)
    
    key_func = functools.cmp_to_key(nan_cmp)
    
    # Test with regular values
    normal1 = key_func(1)
    normal2 = key_func(2)
    assert normal1 < normal2
    
    # Test with "NaN"
    nan1 = key_func("nan")
    nan2 = key_func("nan")
    
    # Should be equal to itself (same comparison)
    assert nan1 == nan1
    
    # But different instances might not be equal
    # This is testing that cmp_to_key handles this correctly
    comparison_result = nan1 == nan2
    # Should handle this without crashing


# Test 9: reduce with very large numbers
@given(st.lists(st.integers(min_value=10**10, max_value=10**15), min_size=2, max_size=10))
def test_reduce_large_numbers(numbers):
    """reduce should handle large number arithmetic correctly"""
    
    # Test multiplication with large numbers
    result = functools.reduce(operator.mul, numbers)
    
    # Manually verify
    expected = numbers[0]
    for n in numbers[1:]:
        expected *= n
    
    assert result == expected


# Test 10: wraps with classes
def test_wraps_with_class():
    """wraps should handle wrapping classes"""
    
    class OriginalClass:
        """Original class docstring"""
        pass
    
    @functools.wraps(OriginalClass)
    class WrapperClass:
        """Wrapper class docstring"""
        pass
    
    # Should have copied attributes
    assert WrapperClass.__doc__ == "Original class docstring"
    assert WrapperClass.__name__ == "OriginalClass"
    assert WrapperClass.__wrapped__ is OriginalClass


# Test 11: recursive_repr with multiple recursive paths
def test_recursive_repr_multiple_paths():
    """recursive_repr should handle multiple recursive references"""
    
    class Node:
        def __init__(self, name):
            self.name = name
            self.left = None
            self.right = None
        
        @functools.recursive_repr()
        def __repr__(self):
            return f"Node({self.name}, L={self.left!r}, R={self.right!r})"
    
    # Create a structure with multiple recursive paths
    root = Node("root")
    child = Node("child")
    
    root.left = child
    root.right = child
    child.left = root  # Back reference
    
    # Should handle this without infinite recursion
    repr_str = repr(root)
    assert "..." in repr_str


# Test 12: cached_property deletion and re-access
def test_cached_property_delete_recompute():
    """cached_property should recompute after deletion"""
    
    compute_count = 0
    
    class MyClass:
        @functools.cached_property
        def value(self):
            nonlocal compute_count
            compute_count += 1
            return compute_count
    
    obj = MyClass()
    
    # First access
    val1 = obj.value
    assert val1 == 1
    assert compute_count == 1
    
    # Delete cached value
    del obj.value
    
    # Next access should recompute
    val2 = obj.value
    assert val2 == 2
    assert compute_count == 2
    
    # Should stay cached
    val3 = obj.value
    assert val3 == 2
    assert compute_count == 2


import weakref  # Add at the top of the file