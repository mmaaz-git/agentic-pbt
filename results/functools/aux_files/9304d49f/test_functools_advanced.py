"""Advanced property-based tests for functools module - looking for edge cases"""
import functools
import operator
import pickle
from hypothesis import given, strategies as st, assume, settings, example
import math
import sys
import weakref
import gc


# Test 1: partial with keyword argument conflicts
@given(st.integers(), st.integers())
def test_partial_keyword_override(a, b):
    """Partial should handle keyword argument overrides correctly"""
    def func(x, y=10, z=20):
        return x + y + z
    
    # Create partial with y specified
    p = functools.partial(func, y=a)
    
    # Call with another y value - should override
    result = p(1, y=b, z=5)
    expected = 1 + b + 5  # The passed y=b should override partial's y=a
    
    assert result == expected


# Test 2: lru_cache with mutable default arguments
@given(st.lists(st.integers()))
def test_lru_cache_mutable_defaults(lst):
    """lru_cache should handle functions with mutable defaults correctly"""
    
    @functools.lru_cache(maxsize=128)
    def append_to_list(x, result=None):
        if result is None:
            result = []
        result.append(x)
        return result
    
    # Each call with default should get fresh list
    result1 = append_to_list(1)
    result2 = append_to_list(2)
    
    # These should be different lists since None triggers new list creation
    assert result1 == [1]
    assert result2 == [2]


# Test 3: reduce with generator that raises
@given(st.integers(min_value=1, max_value=10))
def test_reduce_generator_exception(n):
    """reduce should handle generators that raise exceptions properly"""
    def failing_gen():
        for i in range(n):
            if i == n - 1:
                raise ValueError("Generator failed")
            yield i
    
    try:
        functools.reduce(operator.add, failing_gen(), 0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "Generator failed"


# Test 4: cmp_to_key with inconsistent comparison
def test_cmp_to_key_inconsistent():
    """Test cmp_to_key with non-transitive comparison function"""
    # Rock-paper-scissors comparison (non-transitive)
    def rps_cmp(a, b):
        if a == b:
            return 0
        wins = {('rock', 'scissors'), ('scissors', 'paper'), ('paper', 'rock')}
        if (a, b) in wins:
            return 1
        return -1
    
    key_func = functools.cmp_to_key(rps_cmp)
    
    items = ['rock', 'paper', 'scissors']
    keyed = [key_func(x) for x in items]
    
    # This comparison is non-transitive: rock > scissors, scissors > paper, paper > rock
    rock, paper, scissors = keyed
    
    # Check the non-transitive property exists
    assert rock > scissors
    assert scissors > paper  
    assert paper > rock  # Circular!
    
    # But sorting should still work (though order may be implementation-dependent)
    sorted_items = sorted(items, key=key_func)
    assert len(sorted_items) == 3
    assert set(sorted_items) == set(items)


# Test 5: total_ordering with NotImplemented
@given(st.integers(), st.text())
def test_total_ordering_type_safety(num, text):
    """total_ordering should handle type mismatches correctly"""
    
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
    
    n = Number(num)
    
    # Comparing with incompatible type should return NotImplemented properly
    try:
        result = n < text  # Should raise TypeError
        assert False, f"Should raise TypeError, got {result}"
    except TypeError:
        pass  # Expected
    
    try:
        result = n > text
        assert False, f"Should raise TypeError, got {result}"
    except TypeError:
        pass  # Expected


# Test 6: cache with unhashable arguments
def test_cache_unhashable():
    """cache should fail appropriately with unhashable arguments"""
    
    @functools.cache
    def process_list(lst):
        return sum(lst)
    
    # Should raise TypeError for unhashable type (list)
    try:
        process_list([1, 2, 3])
        assert False, "Should raise TypeError for unhashable argument"
    except TypeError as e:
        assert "unhashable type" in str(e)


# Test 7: partial pickling and unpickling
@given(st.integers(), st.integers())
def test_partial_pickle_roundtrip(a, b):
    """partial objects should pickle and unpickle correctly"""
    def add(x, y):
        return x + y
    
    p = functools.partial(add, a)
    
    # Pickle and unpickle
    pickled = pickle.dumps(p)
    p2 = pickle.loads(pickled)
    
    # Should work the same
    assert p(b) == p2(b)
    assert p(b) == a + b


# Test 8: reduce with single element and no initial
@given(st.integers())
def test_reduce_single_element(x):
    """reduce with single element should return that element"""
    result = functools.reduce(operator.add, [x])
    assert result == x


# Test 9: lru_cache typed parameter
@given(st.integers(), st.floats(allow_nan=False, allow_infinity=False))
def test_lru_cache_typed(i, f):
    """lru_cache with typed=True should distinguish between types"""
    call_count = 0
    
    @functools.lru_cache(maxsize=128, typed=True)
    def identity(x):
        nonlocal call_count
        call_count += 1
        return x
    
    # Call with int
    result_int = identity(5)
    count_after_int = call_count
    
    # Call with float of same value - should be separate cache entry
    result_float = identity(5.0)
    count_after_float = call_count
    
    if count_after_int == 1:
        # If typed=True works correctly, float call should increment counter
        assert count_after_float == 2, "typed=True should treat 5 and 5.0 as different"
    
    # Calling again with same types should use cache
    identity(5)
    assert call_count == count_after_float  # No new calls
    
    identity(5.0)
    assert call_count == count_after_float  # No new calls


# Test 10: partialmethod with class methods
def test_partialmethod_classmethod():
    """partialmethod should work with classmethods"""
    
    class Calculator:
        @classmethod
        def add(cls, a, b, c=0):
            return a + b + c
        
        add_10 = functools.partialmethod(add, b=10)
    
    calc = Calculator()
    
    # Should work on instance
    result = calc.add_10(5)
    assert result == 15
    
    # Should also work on class
    result = Calculator.add_10(5)
    assert result == 15


# Test 11: wraps preserving attributes
@given(st.text(), st.text())
def test_wraps_attribute_preservation(doc, name):
    """wraps should correctly preserve function attributes"""
    assume(name.isidentifier() and not name.startswith('_'))
    
    def original():
        pass
    
    # Set custom attributes
    original.__doc__ = doc
    original.__name__ = name
    original.custom_attr = "test"
    
    @functools.wraps(original)
    def wrapper():
        return original()
    
    # Check preserved attributes
    assert wrapper.__doc__ == doc
    assert wrapper.__name__ == name
    assert wrapper.__wrapped__ is original
    
    # Custom attributes in __dict__ should not be copied by default
    assert not hasattr(wrapper, 'custom_attr')


# Test 12: update_wrapper with missing attributes
def test_update_wrapper_missing_attrs():
    """update_wrapper should handle missing attributes gracefully"""
    
    class Callable:
        def __call__(self):
            return "called"
    
    original = Callable()
    
    def wrapper():
        return original()
    
    # Should not fail even though Callable lacks many attributes
    functools.update_wrapper(wrapper, original)
    
    # __wrapped__ should still be set
    assert wrapper.__wrapped__ is original


# Test 13: cmp_to_key hash behavior
@given(st.integers())
def test_cmp_to_key_hash(x):
    """cmp_to_key objects should not be hashable"""
    def cmp(a, b):
        return (a > b) - (a < b)
    
    key_func = functools.cmp_to_key(cmp)
    obj = key_func(x)
    
    # Should not be hashable
    try:
        hash(obj)
        assert False, "cmp_to_key objects should not be hashable"
    except TypeError:
        pass  # Expected