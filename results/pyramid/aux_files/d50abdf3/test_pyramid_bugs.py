#!/usr/bin/env python3
"""
Property-based tests for finding bugs in pyramid_decorator module.
"""

import functools
import inspect
import json
import sys
from typing import Any, Callable

from hypothesis import assume, given, settings, strategies as st

sys.path.insert(0, '/root/hypothesis-llm/worker_/7')
import pyramid_decorator


# Test 1: reify deletion and re-access property
@given(
    first_value=st.integers() | st.floats(allow_nan=False) | st.text(),
    second_value=st.integers() | st.floats(allow_nan=False) | st.text()
)
def test_reify_delete_recompute(first_value, second_value):
    """Property: After deleting a reified attribute, accessing it should recompute."""
    assume(first_value != second_value)
    
    call_count = []
    values = [first_value, second_value]
    
    class TestClass:
        @pyramid_decorator.reify
        def computed(self):
            call_count.append(1)
            return values[len(call_count) - 1]
    
    obj = TestClass()
    
    # First access should call function and cache
    result1 = obj.computed
    assert len(call_count) == 1
    assert result1 == first_value
    
    # Delete the cached attribute
    delattr(obj, 'computed')
    
    # Next access should recompute with new value
    result2 = obj.computed
    assert len(call_count) == 2
    assert result2 == second_value


# Test 2: compose decorator ordering
@given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=5))
def test_compose_decorator_order_property(multipliers):
    """Property: compose(a, b, c)(func) should equal a(b(c(func)))"""
    
    def make_multiplier(n):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(x):
                return func(x) * n
            return wrapper
        return decorator
    
    def base_func(x):
        return x
    
    # Test the compose function
    decorators = [make_multiplier(m) for m in multipliers]
    composed_func = pyramid_decorator.compose(*decorators)(base_func)
    
    # Manually apply decorators in the documented order
    manual_func = base_func
    for dec in reversed(decorators):
        manual_func = dec(manual_func)
    
    # They should produce the same result
    test_value = 1
    assert composed_func(test_value) == manual_func(test_value)


# Test 3: view_config JSON round-trip property
@given(
    # JSON-serializable values
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers() | st.text(), max_size=10),
        st.dictionaries(st.text(), st.integers() | st.text(), max_size=10)
    )
)
def test_view_config_json_roundtrip(value):
    """Property: JSON renderer should produce parseable JSON that round-trips."""
    
    @pyramid_decorator.view_config(renderer='json')
    def view_func():
        return value
    
    result = view_func()
    
    # Result should be a JSON string
    assert isinstance(result, str)
    
    # Should be valid JSON that round-trips
    parsed = json.loads(result)
    assert parsed == value


# Test 4: validate_arguments should always validate all arguments
@given(
    st.dictionaries(
        st.sampled_from(['a', 'b', 'c']),
        st.integers(min_value=0, max_value=100),
        min_size=1,
        max_size=3
    )
)
def test_validate_arguments_all_validators_called(arg_values):
    """Property: All validators should be called for their respective arguments."""
    
    called_validators = []
    
    def make_validator(name):
        def validator(value):
            called_validators.append(name)
            return value < 50  # Validation rule
        return validator
    
    validators = {name: make_validator(name) for name in arg_values.keys()}
    
    @pyramid_decorator.validate_arguments(**validators)
    def func(**kwargs):
        return sum(kwargs.values())
    
    # Check if any value will fail validation
    will_fail = any(v >= 50 for v in arg_values.values())
    
    called_validators.clear()
    
    if will_fail:
        try:
            func(**arg_values)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
    else:
        result = func(**arg_values)
        assert result == sum(arg_values.values())
    
    # All validators for provided arguments should have been called
    assert set(called_validators) == set(arg_values.keys())


# Test 5: Decorator class callback ordering
@given(
    st.lists(st.integers(), min_size=1, max_size=5),
    st.integers()
)
def test_decorator_callback_order(callback_ids, return_value):
    """Property: Callbacks should be executed in the order they were added."""
    
    execution_order = []
    
    def make_callback(id_val):
        def callback(wrapped, args, kwargs):
            execution_order.append(id_val)
        return callback
    
    decorator = pyramid_decorator.Decorator()
    for id_val in callback_ids:
        decorator.add_callback(make_callback(id_val))
    
    @decorator
    def func():
        return return_value
    
    execution_order.clear()
    result = func()
    
    # Check callbacks were executed in order
    assert execution_order == callback_ids
    assert result == return_value


# Test 6: cached_property delete and recompute
@given(
    st.lists(st.integers() | st.text(), min_size=2, max_size=5)
)
def test_cached_property_delete_behavior(values):
    """Property: cached_property should recompute after deletion."""
    
    call_count = []
    
    class TestClass:
        @pyramid_decorator.cached_property
        def prop(self):
            call_count.append(1)
            return values[len(call_count) - 1] if len(call_count) <= len(values) else None
    
    obj = TestClass()
    
    # First access
    result1 = obj.prop
    assert len(call_count) == 1
    assert result1 == values[0]
    
    # Delete the cached value
    del obj.prop
    
    # Should recompute on next access
    result2 = obj.prop
    assert len(call_count) == 2
    assert result2 == values[1]


# Test 7: preserve_signature actually preserves signature
@given(
    st.lists(st.sampled_from(['a', 'b', 'c', 'd']), min_size=1, max_size=4, unique=True),
    st.dictionaries(
        st.sampled_from(['a', 'b', 'c', 'd']),
        st.sampled_from([int, str, float, bool]),
        max_size=4
    )
)
def test_preserve_signature_preservation(param_names, annotations):
    """Property: preserve_signature should copy signature exactly."""
    
    # Create a function with specific signature
    params = [inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD) 
              for name in param_names]
    sig = inspect.Signature(parameters=params)
    
    def original_func(*args, **kwargs):
        return args, kwargs
    
    original_func.__signature__ = sig
    original_func.__annotations__ = annotations
    
    @pyramid_decorator.preserve_signature(original_func)
    def wrapper(*args, **kwargs):
        return original_func(*args, **kwargs)
    
    # Signature should be preserved
    assert wrapper.__signature__ == original_func.__signature__
    assert wrapper.__annotations__ == original_func.__annotations__


if __name__ == "__main__":
    # Run all tests
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))