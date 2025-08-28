import pytest
from hypothesis import given, strategies as st, assume
import cryptography.utils as utils


class Counter:
    """Helper class to track function calls"""
    def __init__(self):
        self.count = 0
        self.values = []
    
    def increment(self, value):
        self.count += 1
        self.values.append(value)
        return value


@given(st.integers())
def test_cached_property_caches_result(x):
    """Test that cached_property only calls function once"""
    counter = Counter()
    
    class TestClass:
        @utils.cached_property
        def prop(self):
            return counter.increment(x)
    
    obj = TestClass()
    
    # First access
    result1 = obj.prop
    assert result1 == x
    assert counter.count == 1
    
    # Second access - should use cache
    result2 = obj.prop
    assert result2 == x
    assert counter.count == 1  # Still 1, not 2
    
    # Multiple accesses
    for _ in range(10):
        assert obj.prop == x
    assert counter.count == 1  # Still just 1


@given(st.lists(st.integers(), min_size=2, max_size=10))
def test_cached_property_different_instances(values):
    """Test that different instances have separate caches"""
    counter = Counter()
    
    class TestClass:
        def __init__(self, value):
            self.value = value
        
        @utils.cached_property
        def prop(self):
            return counter.increment(self.value)
    
    # Create multiple instances
    instances = [TestClass(v) for v in values]
    
    # Access property on each instance
    results = []
    for i, obj in enumerate(instances):
        result = obj.prop
        results.append(result)
        assert result == values[i]
    
    # Verify each instance was called once
    assert counter.count == len(values)
    
    # Access again - should use cache
    for i, obj in enumerate(instances):
        assert obj.prop == values[i]
    
    # Count shouldn't have increased
    assert counter.count == len(values)


@given(st.integers(), st.integers())
def test_cached_property_mutation(initial, updated):
    """Test behavior when underlying data changes"""
    class TestClass:
        def __init__(self):
            self.data = initial
        
        @utils.cached_property
        def computed(self):
            return self.data * 2
    
    obj = TestClass()
    
    # First access
    assert obj.computed == initial * 2
    
    # Change underlying data
    obj.data = updated
    
    # Property should still return cached value (not updated * 2)
    assert obj.computed == initial * 2
    
    # This demonstrates that cached_property doesn't detect mutations


@given(st.integers())
def test_cached_property_deleting_cache(x):
    """Test that deleting the cache allows recalculation"""
    counter = Counter()
    
    class TestClass:
        @utils.cached_property
        def prop(self):
            return counter.increment(x)
    
    obj = TestClass()
    
    # First access
    assert obj.prop == x
    assert counter.count == 1
    
    # Delete the cached attribute
    delattr(obj, '_cached_prop')
    
    # Next access should recalculate
    assert obj.prop == x
    assert counter.count == 2


@given(st.text(min_size=1), st.integers())
def test_cached_property_with_different_names(name, value):
    """Test that cached_property works with arbitrary property names"""
    # Filter out names that would be invalid Python identifiers
    assume(name.isidentifier())
    assume(not name.startswith('_'))
    
    counter = Counter()
    
    # Dynamically create class with property of given name
    class_dict = {
        name: utils.cached_property(lambda self: counter.increment(value))
    }
    TestClass = type('TestClass', (), class_dict)
    
    obj = TestClass()
    
    # Access the property
    result = getattr(obj, name)
    assert result == value
    assert counter.count == 1
    
    # Access again - should be cached
    result2 = getattr(obj, name)
    assert result2 == value
    assert counter.count == 1
    
    # Check the cached attribute name
    cached_name = f'_cached_{name}'
    assert hasattr(obj, cached_name)
    assert getattr(obj, cached_name) == value


@given(st.lists(st.integers(), min_size=1))
def test_cached_property_preserves_exceptions(values):
    """Test that exceptions are not cached"""
    call_count = [0]
    
    class TestClass:
        @utils.cached_property
        def prop(self):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ValueError("First call fails")
            return values[0]
    
    obj = TestClass()
    
    # First access should raise
    with pytest.raises(ValueError):
        obj.prop
    
    # Second access should retry (not cache the exception)
    result = obj.prop
    assert result == values[0]
    assert call_count[0] == 2
    
    # Third access should use cache
    result = obj.prop
    assert result == values[0]
    assert call_count[0] == 2