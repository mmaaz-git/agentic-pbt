"""Property-based tests for functools module"""
import functools
import operator
from hypothesis import given, strategies as st, assume, settings
import math


# Test 1: reduce with associative operations
@given(st.lists(st.integers(), min_size=1))
def test_reduce_associativity_sum(lst):
    """reduce should give same result as builtin sum for addition"""
    result_reduce = functools.reduce(operator.add, lst)
    result_sum = sum(lst)
    assert result_reduce == result_sum


@given(st.lists(st.integers(min_value=1, max_value=100), min_size=1))
def test_reduce_associativity_product(lst):
    """reduce with multiplication should give same result as math.prod"""
    result_reduce = functools.reduce(operator.mul, lst)
    result_prod = math.prod(lst)
    assert result_reduce == result_prod


# Test 2: partial function application consistency
@given(st.integers(min_value=0, max_value=100000), 
       st.integers(min_value=2, max_value=36))
def test_partial_application_consistency(x, base):
    """partial(int, base=b)(str(x)) should equal int(str(x), b) for valid bases"""
    # Convert x to valid string representation in given base
    if base <= 10:
        # For bases <= 10, use only digits that are valid
        str_x = str(x)
        # Filter to only valid digits for this base
        valid_digits = ''.join(d for d in str_x if int(d) < base)
        if not valid_digits:
            valid_digits = '0'
    else:
        # For simplicity with larger bases, just use base 10 representation
        valid_digits = str(x)
    
    partial_int = functools.partial(int, base=base)
    
    # Both should parse the same way
    result1 = partial_int(valid_digits)
    result2 = int(valid_digits, base)
    assert result1 == result2


# Test 3: cmp_to_key transitivity property
@given(st.lists(st.integers(), min_size=3, max_size=10))
def test_cmp_to_key_transitivity(lst):
    """cmp_to_key should maintain transitivity of comparisons"""
    def cmp(a, b):
        return (a > b) - (a < b)
    
    key_func = functools.cmp_to_key(cmp)
    
    # Convert all elements using the key function
    keyed_items = [key_func(x) for x in lst]
    
    # Check transitivity: if a < b and b < c, then a < c
    for i in range(len(keyed_items)):
        for j in range(len(keyed_items)):
            for k in range(len(keyed_items)):
                a, b, c = keyed_items[i], keyed_items[j], keyed_items[k]
                if a < b and b < c:
                    assert a < c, f"Transitivity violated: {lst[i]} < {lst[j]} < {lst[k]}"


# Test 4: cmp_to_key consistency with sorting
@given(st.lists(st.integers()))
def test_cmp_to_key_sorting_consistency(lst):
    """Sorting with cmp_to_key should match regular sorting"""
    def cmp(a, b):
        return (a > b) - (a < b)
    
    key_func = functools.cmp_to_key(cmp)
    
    sorted_with_key = sorted(lst, key=key_func)
    sorted_regular = sorted(lst)
    
    assert sorted_with_key == sorted_regular


# Test 5: lru_cache correctness
@given(st.integers(), st.integers())
def test_lru_cache_correctness(x, y):
    """lru_cache should not change function results"""
    call_count = 0
    
    def uncached_add(a, b):
        nonlocal call_count
        call_count += 1
        return a + b
    
    cached_add = functools.lru_cache(maxsize=128)(uncached_add)
    
    # First call
    result1 = cached_add(x, y)
    count_after_first = call_count
    
    # Second call (should be cached)
    result2 = cached_add(x, y)
    count_after_second = call_count
    
    # Results should be the same
    assert result1 == result2
    assert result1 == x + y
    
    # Second call should not increase call count (it's cached)
    assert count_after_second == count_after_first


# Test 6: cache decorator correctness
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_cache_correctness(x):
    """cache decorator should preserve function behavior"""
    
    @functools.cache
    def cached_square(n):
        return n * n
    
    def uncached_square(n):
        return n * n
    
    cached_result = cached_square(x)
    uncached_result = uncached_square(x)
    
    assert math.isclose(cached_result, uncached_result, rel_tol=1e-9)


# Test 7: reduce with empty sequence and initial value
@given(st.integers())
def test_reduce_empty_with_initial(initial):
    """reduce with empty sequence and initial value should return initial"""
    result = functools.reduce(operator.add, [], initial)
    assert result == initial


# Test 8: partial with nested partials
@given(st.integers(), st.integers(), st.integers())
def test_partial_nested(a, b, c):
    """Nested partials should flatten correctly"""
    def add3(x, y, z):
        return x + y + z
    
    # Create nested partials
    p1 = functools.partial(add3, a)
    p2 = functools.partial(p1, b)
    
    # Should work the same as direct application
    result1 = p2(c)
    result2 = add3(a, b, c)
    
    assert result1 == result2


# Test 9: reduce invariant - order matters for non-associative operations
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False, min_value=0.1, max_value=10), 
                min_size=2, max_size=5))
def test_reduce_order_matters(lst):
    """reduce should apply operations left-to-right"""
    # Division is not associative, so order matters
    result = functools.reduce(operator.truediv, lst)
    
    # Manually compute left-to-right
    manual_result = lst[0]
    for val in lst[1:]:
        manual_result = manual_result / val
    
    assert math.isclose(result, manual_result, rel_tol=1e-9)


# Test 10: Test total_ordering decorator
@given(st.integers(), st.integers())
def test_total_ordering_consistency(x, y):
    """total_ordering should create consistent comparison methods"""
    
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
    b = Number(y)
    
    # Check consistency of generated methods
    if a < b:
        assert b > a  # __gt__ should be consistent with __lt__
        assert a <= b  # __le__ should be consistent with __lt__
        assert not (a >= b)  # __ge__ should be consistent
        assert a != b  # Different values
    elif a > b:
        assert b < a
        assert a >= b
        assert not (a <= b)
        assert a != b
    else:  # a == b
        assert not (a < b)
        assert not (a > b)
        assert a <= b
        assert a >= b
        assert a == b


# Test 11: cmp_to_key edge case with equal elements
@given(st.lists(st.integers(min_value=0, max_value=5), min_size=2))
def test_cmp_to_key_equal_elements(lst):
    """cmp_to_key should handle equal elements correctly"""
    def cmp(a, b):
        return (a > b) - (a < b)
    
    key_func = functools.cmp_to_key(cmp)
    keyed = [key_func(x) for x in lst]
    
    for i, ki in enumerate(keyed):
        for j, kj in enumerate(keyed):
            if lst[i] == lst[j]:
                # Equal elements should compare as equal
                assert ki == kj
                assert not (ki < kj)
                assert not (ki > kj)
                assert ki <= kj
                assert ki >= kj