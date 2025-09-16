"""Edge case property-based tests for functools"""
import functools
import operator
from hypothesis import given, strategies as st, assume, settings
import sys


# Test 1: singledispatch with inheritance
def test_singledispatch_inheritance():
    """singledispatch should handle inheritance correctly"""
    
    @functools.singledispatch
    def process(arg):
        return f"default: {arg}"
    
    @process.register
    def _(arg: int):
        return f"int: {arg}"
    
    @process.register
    def _(arg: list):
        return f"list: {arg}"
    
    class MyList(list):
        pass
    
    # MyList should use list handler due to inheritance
    ml = MyList([1, 2, 3])
    result = process(ml)
    assert result == "list: [1, 2, 3]"
    
    # bool is subclass of int
    result = process(True)
    assert result == "int: True"


# Test 2: singledispatch with None
def test_singledispatch_none():
    """singledispatch should handle None specially"""
    
    @functools.singledispatch
    def process(arg):
        return f"default: {arg}"
    
    @process.register(type(None))
    def _(arg):
        return "None value"
    
    assert process(None) == "None value"
    assert process(0) == "default: 0"


# Test 3: cached_property thread safety
def test_cached_property_basic():
    """cached_property should cache correctly"""
    call_count = 0
    
    class Calculator:
        @functools.cached_property
        def expensive_value(self):
            nonlocal call_count
            call_count += 1
            return 42
    
    calc = Calculator()
    
    # First access
    val1 = calc.expensive_value
    assert val1 == 42
    assert call_count == 1
    
    # Second access should use cache
    val2 = calc.expensive_value
    assert val2 == 42
    assert call_count == 1  # Should not increment
    
    # Delete cached value
    del calc.expensive_value
    
    # Next access should recompute
    val3 = calc.expensive_value
    assert val3 == 42
    assert call_count == 2


# Test 4: reduce with custom exceptions in function
@given(st.lists(st.integers(min_value=1, max_value=100), min_size=2))
def test_reduce_exception_propagation(lst):
    """reduce should properly propagate exceptions from the reduction function"""
    
    def divider(a, b):
        if b == 13:  # Unlucky number
            raise ValueError("Unlucky 13!")
        return a // b if b != 0 else a
    
    if 13 in lst[1:]:  # 13 in positions that will be used as divisor
        try:
            functools.reduce(divider, lst)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert str(e) == "Unlucky 13!"
    else:
        # Should complete normally
        result = functools.reduce(divider, lst)
        assert isinstance(result, int)


# Test 5: lru_cache maxsize edge cases
def test_lru_cache_maxsize_zero():
    """lru_cache with maxsize=0 should not cache"""
    call_count = 0
    
    @functools.lru_cache(maxsize=0)
    def increment():
        nonlocal call_count
        call_count += 1
        return call_count
    
    # Each call should increment
    assert increment() == 1
    assert increment() == 2
    assert increment() == 3
    
    # Check cache info
    info = increment.cache_info()
    assert info.maxsize == 0
    assert info.currsize == 0
    assert info.hits == 0
    assert info.misses == 3


# Test 6: lru_cache with maxsize=1
@given(st.integers(), st.integers())
def test_lru_cache_maxsize_one(a, b):
    """lru_cache with maxsize=1 should only keep last item"""
    assume(a != b)
    
    call_count = 0
    
    @functools.lru_cache(maxsize=1)
    def identity(x):
        nonlocal call_count
        call_count += 1
        return x
    
    # First call
    identity(a)
    count_after_first = call_count
    assert count_after_first == 1
    
    # Call with same value - should hit cache
    identity(a)
    assert call_count == 1  # No new call
    
    # Call with different value - evicts previous
    identity(b)
    assert call_count == 2
    
    # Call first value again - cache miss (was evicted)
    identity(a)
    assert call_count == 3


# Test 7: partial with no arguments
def test_partial_no_args():
    """partial with no partial args should work like original function"""
    def add(a, b):
        return a + b
    
    p = functools.partial(add)  # No partial arguments
    
    assert p(2, 3) == 5
    assert p(2, 3) == add(2, 3)


# Test 8: partial __setstate__ validation
def test_partial_setstate_validation():
    """partial.__setstate__ should validate its input"""
    
    def dummy():
        pass
    
    p = functools.partial(dummy)
    
    # Invalid state - not a tuple
    try:
        p.__setstate__("not a tuple")
        assert False, "Should raise TypeError"
    except TypeError as e:
        assert "must be a tuple" in str(e)
    
    # Invalid state - wrong length
    try:
        p.__setstate__((dummy, (), {}))  # Only 3 items instead of 4
        assert False, "Should raise TypeError"
    except TypeError as e:
        assert "expected 4 items" in str(e)
    
    # Invalid state - wrong types
    try:
        p.__setstate__((dummy, "not a tuple", {}, {}))
        assert False, "Should raise TypeError"
    except TypeError as e:
        assert "invalid partial state" in str(e)


# Test 9: cmp_to_key comparison with itself
@given(st.integers())
def test_cmp_to_key_self_comparison(x):
    """cmp_to_key objects should compare equal to themselves"""
    def cmp(a, b):
        return (a > b) - (a < b)
    
    key_func = functools.cmp_to_key(cmp)
    obj = key_func(x)
    
    # Should be equal to itself
    assert obj == obj
    assert not (obj < obj)
    assert not (obj > obj)
    assert obj <= obj
    assert obj >= obj


# Test 10: total_ordering with only __eq__ and __ge__
def test_total_ordering_ge_only():
    """total_ordering should work with __ge__ as the comparison method"""
    
    @functools.total_ordering
    class Number:
        def __init__(self, value):
            self.value = value
        
        def __eq__(self, other):
            if not isinstance(other, Number):
                return NotImplemented
            return self.value == other.value
        
        def __ge__(self, other):
            if not isinstance(other, Number):
                return NotImplemented
            return self.value >= other.value
    
    # Test that all comparison methods work
    a = Number(5)
    b = Number(10)
    
    assert not (a > b)
    assert a < b
    assert a <= b
    assert not (a >= b)
    
    c = Number(5)
    assert a == c
    assert a >= c
    assert a <= c


# Test 11: recursive_repr edge case
def test_recursive_repr():
    """recursive_repr should handle recursive structures"""
    
    class Node:
        def __init__(self, value):
            self.value = value
            self.next = None
        
        @functools.recursive_repr()
        def __repr__(self):
            return f"Node({self.value}, next={self.next!r})"
    
    # Create circular reference
    n1 = Node(1)
    n2 = Node(2)
    n1.next = n2
    n2.next = n1  # Circular!
    
    # Should not infinite loop
    repr_str = repr(n1)
    assert "..." in repr_str  # Should contain ellipsis for recursion


# Test 12: update_wrapper edge case with property
def test_update_wrapper_with_property():
    """update_wrapper should handle properties correctly"""
    
    class MyClass:
        @property
        def my_property(self):
            """Property docstring"""
            return 42
    
    def wrapper():
        return MyClass().my_property
    
    # Should handle property objects
    functools.update_wrapper(wrapper, MyClass.my_property)
    
    # Check that wrapper got property's attributes
    assert wrapper.__doc__ == "Property docstring"