"""Complex property tests for functools - testing algorithmic properties"""
import functools
import operator
from hypothesis import given, strategies as st, assume, settings
import weakref
import gc


# Test 1: _c3_merge algorithm correctness
def test_c3_merge_inconsistent_hierarchy():
    """_c3_merge should detect inconsistent hierarchies"""
    # This creates an inconsistent hierarchy that cannot be linearized
    # A depends on B before C, but another path requires C before B
    sequences = [
        ['A', 'B', 'C'],
        ['A', 'C', 'B'],
    ]
    
    try:
        result = functools._c3_merge(sequences)
        assert False, f"Should raise RuntimeError for inconsistent hierarchy, got {result}"
    except RuntimeError as e:
        assert "Inconsistent hierarchy" in str(e)


# Test 2: singledispatchmethod with inheritance
def test_singledispatchmethod():
    """singledispatchmethod should work correctly with methods"""
    
    class Processor:
        @functools.singledispatchmethod
        def process(self, arg):
            return f"default: {arg}"
        
        @process.register
        def _(self, arg: int):
            return f"int: {arg}"
        
        @process.register
        def _(self, arg: str):
            return f"str: {arg}"
    
    p = Processor()
    
    assert p.process(42) == "int: 42"
    assert p.process("hello") == "str: hello"
    assert p.process([1, 2]) == "default: [1, 2]"


# Test 3: cached_property with __slots__
def test_cached_property_with_slots():
    """cached_property should work with __slots__ classes"""
    
    class SlottedClass:
        __slots__ = ('_expensive_value',)
        
        @functools.cached_property
        def expensive_value(self):
            return 42
    
    obj = SlottedClass()
    
    # Should work even with __slots__
    assert obj.expensive_value == 42
    
    # Should be cached (check by accessing again)
    assert obj.expensive_value == 42


# Test 4: reduce behavior with StopIteration
def test_reduce_stop_iteration():
    """reduce should handle StopIteration in the iterable correctly"""
    
    class StoppingIterable:
        def __iter__(self):
            yield 1
            yield 2
            raise StopIteration("Custom message")
    
    # reduce should handle StopIteration gracefully
    result = functools.reduce(operator.add, StoppingIterable())
    assert result == 3  # 1 + 2


# Test 5: lru_cache with weakref keys
def test_lru_cache_weakref():
    """Test lru_cache behavior with objects that can be weakly referenced"""
    
    class MyClass:
        def __init__(self, value):
            self.value = value
        
        def __hash__(self):
            return hash(self.value)
        
        def __eq__(self, other):
            return isinstance(other, MyClass) and self.value == other.value
    
    @functools.lru_cache(maxsize=128)
    def process(obj):
        return obj.value * 2
    
    obj1 = MyClass(5)
    result1 = process(obj1)
    assert result1 == 10
    
    # Create another object with same hash/equality
    obj2 = MyClass(5)
    result2 = process(obj2)
    assert result2 == 10
    
    # Should have hit cache
    info = process.cache_info()
    assert info.hits == 1
    assert info.misses == 1


# Test 6: partial with descriptor protocol
def test_partial_descriptor_warning():
    """partial should warn about descriptor usage"""
    import warnings
    
    class MyClass:
        def method(self, x, y):
            return x + y
        
        # Using partial as a descriptor (will warn in future)
        partial_method = functools.partial(method, y=10)
    
    obj = MyClass()
    
    # Should trigger FutureWarning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = obj.partial_method(obj, 5)  # Need to pass self explicitly
        
        # Check warning was raised
        assert len(w) == 1
        assert issubclass(w[0].category, FutureWarning)
        assert "method descriptor" in str(w[0].message)
    
    assert result == 15


# Test 7: Complex singledispatch with ABC
def test_singledispatch_abc():
    """singledispatch should work with abstract base classes"""
    from collections.abc import Sequence, Mapping
    
    @functools.singledispatch
    def process(arg):
        return "default"
    
    @process.register(Sequence)
    def _(arg):
        return f"sequence: {list(arg)}"
    
    @process.register(Mapping)
    def _(arg):
        return f"mapping: {dict(arg)}"
    
    # List is a Sequence
    assert process([1, 2, 3]) == "sequence: [1, 2, 3]"
    
    # Tuple is a Sequence
    assert process((1, 2, 3)) == "sequence: [1, 2, 3]"
    
    # Dict is a Mapping
    assert process({'a': 1}) == "mapping: {'a': 1}"
    
    # String is also a Sequence
    assert process("abc") == "sequence: ['a', 'b', 'c']"


# Test 8: total_ordering with complex inheritance
def test_total_ordering_inheritance():
    """total_ordering should work correctly with inheritance"""
    
    @functools.total_ordering
    class Base:
        def __init__(self, value):
            self.value = value
        
        def __eq__(self, other):
            if not isinstance(other, Base):
                return NotImplemented
            return self.value == other.value
        
        def __lt__(self, other):
            if not isinstance(other, Base):
                return NotImplemented
            return self.value < other.value
    
    class Derived(Base):
        pass
    
    # Should work across inheritance
    b = Base(5)
    d = Derived(10)
    
    assert b < d
    assert d > b
    assert b <= d
    assert d >= b


# Test 9: reduce with very long iterables
@given(st.integers(min_value=1000, max_value=10000))
def test_reduce_long_iterable(n):
    """reduce should handle long iterables efficiently"""
    # This tests that reduce doesn't have stack overflow issues
    
    # Create a long iterable
    long_iter = range(n)
    
    # Sum using reduce
    result = functools.reduce(operator.add, long_iter, 0)
    expected = n * (n - 1) // 2  # Sum formula
    
    assert result == expected


# Test 10: lru_cache clear while iterating
def test_lru_cache_clear_during_iteration():
    """lru_cache should handle cache clearing safely"""
    
    @functools.lru_cache(maxsize=128)
    def cached_func(x):
        return x * 2
    
    # Populate cache
    for i in range(10):
        cached_func(i)
    
    # Clear cache
    cached_func.cache_clear()
    
    # Cache should be empty
    info = cached_func.cache_info()
    assert info.currsize == 0
    assert info.hits == 0
    assert info.misses == 0


# Test 11: partialmethod with staticmethod
def test_partialmethod_staticmethod():
    """partialmethod should work with staticmethods"""
    
    class Calculator:
        @staticmethod
        def add(a, b, c=0):
            return a + b + c
        
        add_10 = functools.partialmethod(add, b=10)
    
    # Should work on instance
    calc = Calculator()
    result = calc.add_10(5)
    assert result == 15


# Test 12: Extreme recursion with recursive_repr
def test_recursive_repr_extreme():
    """recursive_repr should handle deeply nested recursion"""
    
    class Node:
        def __init__(self, value):
            self.value = value
            self.children = []
        
        @functools.recursive_repr()
        def __repr__(self):
            return f"Node({self.value}, {self.children})"
    
    # Create a deeply recursive structure
    root = Node(0)
    current = root
    
    # Create a chain
    for i in range(1, 100):
        child = Node(i)
        current.children.append(child)
        current = child
    
    # Make it circular
    current.children.append(root)
    
    # Should not crash
    repr_str = repr(root)
    assert "..." in repr_str  # Should detect recursion