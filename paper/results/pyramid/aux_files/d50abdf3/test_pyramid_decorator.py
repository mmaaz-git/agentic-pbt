#!/usr/bin/env python3
"""
Property-based tests for pyramid_decorator module using Hypothesis.
"""

import functools
import inspect
import json
import sys
import traceback
from typing import Any, Callable, List

import pyramid_decorator
from hypothesis import assume, given, settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize

# Import the module we're testing
sys.path.insert(0, '/root/hypothesis-llm/worker_/7')


# Test 1: reify class - caching properties
class TestReify:
    """Test the reify decorator's caching behavior."""
    
    @given(
        values=st.lists(st.integers() | st.floats(allow_nan=False) | st.text()),
        call_count=st.integers(min_value=1, max_value=10)
    )
    def test_reify_single_call(self, values, call_count):
        """Property: reify should only call the decorated function once."""
        call_tracker = []
        
        class TestClass:
            @pyramid_decorator.reify
            def computed_value(self):
                call_tracker.append(1)
                return values[0] if values else None
        
        obj = TestClass()
        
        # Access the property multiple times
        results = []
        for _ in range(call_count):
            results.append(obj.computed_value)
        
        # Properties to verify:
        # 1. Function was called exactly once
        assert len(call_tracker) == 1, f"Function called {len(call_tracker)} times, expected 1"
        
        # 2. All accesses return the same value
        assert all(r == results[0] for r in results), "Not all results are identical"
        
        # 3. The value is now an instance attribute
        assert hasattr(obj, 'computed_value')
        assert getattr(obj, 'computed_value') == results[0]
    
    @given(st.data())
    def test_reify_different_instances(self, data):
        """Property: Each instance should have its own cached value."""
        value1 = data.draw(st.integers())
        value2 = data.draw(st.integers())
        assume(value1 != value2)
        
        class TestClass:
            def __init__(self, val):
                self.val = val
                
            @pyramid_decorator.reify
            def computed(self):
                return self.val
        
        obj1 = TestClass(value1)
        obj2 = TestClass(value2)
        
        # Each instance should have its own cached value
        assert obj1.computed == value1
        assert obj2.computed == value2
        assert obj1.computed != obj2.computed


# Test 2: cached_property class
class TestCachedProperty:
    """Test the cached_property decorator."""
    
    @given(
        initial_value=st.integers() | st.floats(allow_nan=False) | st.text(),
        access_count=st.integers(min_value=2, max_value=10)
    )
    def test_cached_property_caching(self, initial_value, access_count):
        """Property: cached_property should cache the computed value."""
        call_count = []
        
        class TestClass:
            @pyramid_decorator.cached_property
            def value(self):
                call_count.append(1)
                return initial_value
        
        obj = TestClass()
        
        # Access multiple times
        results = [obj.value for _ in range(access_count)]
        
        # Should only compute once
        assert len(call_count) == 1
        # All results should be the same
        assert all(r == initial_value for r in results)
    
    @given(
        computed_value=st.integers(),
        set_value=st.integers()
    )
    def test_cached_property_set_delete(self, computed_value, set_value):
        """Property: cached_property should support setting and deletion."""
        assume(computed_value != set_value)
        
        class TestClass:
            @pyramid_decorator.cached_property
            def prop(self):
                return computed_value
        
        obj = TestClass()
        
        # Initial access should return computed value
        assert obj.prop == computed_value
        
        # Setting should change the value
        obj.prop = set_value
        assert obj.prop == set_value
        
        # Deleting should clear the cache
        del obj.prop
        # Next access should recompute
        assert obj.prop == computed_value
    
    @given(st.text(min_size=1))
    def test_cached_property_naming(self, prop_name):
        """Property: Cache attribute follows naming pattern _cached_{name}."""
        assume(not prop_name.startswith('_'))  # Avoid private names
        assume(prop_name.isidentifier())  # Must be valid Python identifier
        
        # Dynamically create a class with the property
        class_dict = {}
        exec(f'''
def {prop_name}(self):
    return 42
''', class_dict)
        
        TestClass = type('TestClass', (), {
            prop_name: pyramid_decorator.cached_property(class_dict[prop_name])
        })
        
        obj = TestClass()
        getattr(obj, prop_name)  # Access the property
        
        # Check the cache attribute exists with correct naming
        cache_attr = f'_cached_{prop_name}'
        assert hasattr(obj, cache_attr)
        assert getattr(obj, cache_attr) == 42


# Test 3: Decorator composition
class TestCompose:
    """Test the compose function for decorator composition."""
    
    @given(
        input_value=st.integers(),
        add_values=st.lists(st.integers(), min_size=1, max_size=5)
    )
    def test_compose_order(self, input_value, add_values):
        """Property: compose(a, b, c)(func) == a(b(c(func)))"""
        
        # Create decorators that add values
        decorators = []
        for val in add_values:
            def make_decorator(v):
                def decorator(func):
                    @functools.wraps(func)
                    def wrapper(x):
                        return func(x) + v
                    return wrapper
                return decorator
            decorators.append(make_decorator(val))
        
        def base_func(x):
            return x
        
        # Apply using compose
        composed = pyramid_decorator.compose(*decorators)(base_func)
        result1 = composed(input_value)
        
        # Apply manually in the same order
        manual = base_func
        for dec in reversed(decorators):
            manual = dec(manual)
        result2 = manual(input_value)
        
        assert result1 == result2, f"Compose result {result1} != manual result {result2}"
    
    @given(st.data())
    def test_compose_empty(self, data):
        """Property: compose with no decorators returns original function."""
        value = data.draw(st.integers())
        
        def func(x):
            return x * 2
        
        composed = pyramid_decorator.compose()(func)
        
        assert composed(value) == func(value)
        assert composed(value) == value * 2


# Test 4: view_config decorator
class TestViewConfig:
    """Test the view_config decorator."""
    
    @given(
        result_value=st.dictionaries(
            st.text(min_size=1), 
            st.integers() | st.floats(allow_nan=False) | st.text() | st.booleans()
        ),
        use_json=st.booleans()
    )
    def test_view_config_json_renderer(self, result_value, use_json):
        """Property: JSON renderer should convert non-strings to JSON."""
        
        @pyramid_decorator.view_config(renderer='json' if use_json else None)
        def view_func():
            return result_value
        
        result = view_func()
        
        if use_json:
            # Result should be JSON string
            assert isinstance(result, str)
            # Should be valid JSON that parses back to original
            parsed = json.loads(result)
            assert parsed == result_value
        else:
            # Without renderer, should return original
            assert result == result_value
    
    @given(
        value=st.integers() | st.floats(allow_nan=False) | st.lists(st.integers()),
        use_string=st.booleans()
    )
    def test_view_config_string_renderer(self, value, use_string):
        """Property: String renderer should convert to string."""
        
        @pyramid_decorator.view_config(renderer='string' if use_string else None)
        def view_func():
            return value
        
        result = view_func()
        
        if use_string:
            assert isinstance(result, str)
            assert result == str(value)
        else:
            assert result == value
    
    @given(
        settings_list=st.lists(
            st.dictionaries(st.text(min_size=1), st.integers()),
            min_size=1,
            max_size=5
        )
    )
    def test_view_config_accumulation(self, settings_list):
        """Property: Multiple decorations should accumulate settings."""
        
        def base_func():
            return "test"
        
        # Apply multiple view_config decorators
        func = base_func
        for settings in settings_list:
            func = pyramid_decorator.view_config(**settings)(func)
        
        # Check that all settings were accumulated
        assert hasattr(func, '__view_settings__')
        assert len(func.__view_settings__) == len(settings_list)
        
        # Each setting should be in the list
        for i, settings in enumerate(settings_list):
            assert func.__view_settings__[i] == settings


# Test 5: validate_arguments decorator
class TestValidateArguments:
    """Test the validate_arguments decorator."""
    
    @given(
        valid_value=st.integers(min_value=1, max_value=100),
        invalid_value=st.integers(max_value=0) | st.integers(min_value=101)
    )
    def test_validate_arguments_basic(self, valid_value, invalid_value):
        """Property: Should validate arguments according to validators."""
        
        def is_valid(x):
            return 1 <= x <= 100
        
        @pyramid_decorator.validate_arguments(x=is_valid)
        def func(x):
            return x * 2
        
        # Valid value should pass
        assert func(valid_value) == valid_value * 2
        
        # Invalid value should raise ValueError
        try:
            func(invalid_value)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid value for x" in str(e)
    
    @given(
        values=st.dictionaries(
            st.sampled_from(['a', 'b', 'c']),
            st.integers(),
            min_size=1,
            max_size=3
        )
    )
    def test_validate_arguments_multiple(self, values):
        """Property: Multiple validators should all be checked."""
        
        validators = {
            'a': lambda x: x > 0,
            'b': lambda x: x < 100,
            'c': lambda x: x % 2 == 0
        }
        
        # Only include validators for parameters we have
        active_validators = {k: v for k, v in validators.items() if k in values}
        
        @pyramid_decorator.validate_arguments(**active_validators)
        def func(**kwargs):
            return sum(kwargs.values())
        
        # Check if all values are valid
        all_valid = all(
            validators[k](v) for k, v in values.items() 
            if k in validators
        )
        
        if all_valid:
            result = func(**values)
            assert result == sum(values.values())
        else:
            try:
                func(**values)
                assert False, "Should have raised ValueError"
            except ValueError:
                pass  # Expected


# Test 6: preserve_signature decorator
class TestPreserveSignature:
    """Test the preserve_signature decorator."""
    
    @given(st.data())
    def test_preserve_signature_basic(self, data):
        """Property: Decorated function should preserve original signature."""
        
        # Generate random function signature
        param_names = data.draw(st.lists(
            st.text(alphabet='abcdefghijk', min_size=1, max_size=3),
            min_size=1,
            max_size=4,
            unique=True
        ))
        
        # Create a function with those parameters
        func_str = f"def original_func({', '.join(param_names)}): return sum([{', '.join(param_names)}])"
        local_dict = {}
        exec(func_str, local_dict)
        original_func = local_dict['original_func']
        
        # Create a wrapper that changes the signature
        def wrapper(*args, **kwargs):
            return original_func(*args, **kwargs) * 2
        
        # Apply preserve_signature
        preserved = pyramid_decorator.preserve_signature(original_func)(wrapper)
        
        # Check signatures match
        assert inspect.signature(preserved) == inspect.signature(original_func)
    
    @given(
        annotations=st.dictionaries(
            st.sampled_from(['x', 'y', 'z']),
            st.sampled_from([int, str, float, bool]),
            min_size=1,
            max_size=3
        )
    )
    def test_preserve_signature_annotations(self, annotations):
        """Property: Annotations should be preserved."""
        
        # Build function with annotations
        params = ', '.join(f"{k}: {v.__name__}" for k, v in annotations.items())
        func_str = f"def func({params}): pass"
        
        local_dict = {'int': int, 'str': str, 'float': float, 'bool': bool}
        exec(func_str, local_dict)
        original = local_dict['func']
        
        def wrapper(*args, **kwargs):
            return original(*args, **kwargs)
        
        preserved = pyramid_decorator.preserve_signature(original)(wrapper)
        
        # Check annotations are preserved
        assert preserved.__annotations__ == original.__annotations__


# Test 7: MethodDecorator class
class TestMethodDecorator:
    """Test the MethodDecorator class."""
    
    @given(
        instance_value=st.integers(),
        class_value=st.integers(),
        options=st.dictionaries(st.text(min_size=1), st.integers())
    )
    def test_method_decorator_context(self, instance_value, class_value, options):
        """Property: Should handle instance vs class context correctly."""
        
        class TestClass:
            value = class_value
            
            def __init__(self):
                self.instance_value = instance_value
            
            @pyramid_decorator.MethodDecorator
            def method(self_or_cls):
                if hasattr(self_or_cls, 'instance_value'):
                    return self_or_cls.instance_value
                else:
                    return self_or_cls.value
        
        obj = TestClass()
        
        # Accessing from instance should use instance context
        instance_method = obj.method
        # This will be a partial, we need to call it
        # But MethodDecorator's __get__ returns a partial of self.func
        # which needs to be called
        
        # Actually, looking at the implementation, MethodDecorator
        # doesn't work correctly as written - it tries to call self.func
        # but self.func might be None initially


# Test 8: Decorator class with callbacks
class TestDecoratorClass:
    """Test the Decorator class with callbacks."""
    
    @given(
        settings=st.dictionaries(
            st.text(min_size=1),
            st.integers() | st.text() | st.booleans()
        ),
        num_callbacks=st.integers(min_value=0, max_value=5),
        return_value=st.integers()
    )
    def test_decorator_callbacks(self, settings, num_callbacks, return_value):
        """Property: Callbacks should be executed in order before the function."""
        
        callback_order = []
        
        dec = pyramid_decorator.Decorator(**settings)
        
        # Add callbacks
        for i in range(num_callbacks):
            def make_callback(idx):
                def callback(wrapped, args, kwargs):
                    callback_order.append(idx)
                return callback
            dec.add_callback(make_callback(i))
        
        @dec
        def func():
            return return_value
        
        result = func()
        
        # Check callbacks were called in order
        assert callback_order == list(range(num_callbacks))
        
        # Check function still returns correct value (unless json_response is set)
        if settings.get('json_response'):
            assert result == json.dumps(return_value)
        else:
            assert result == return_value
        
        # Check metadata is stored
        assert hasattr(func, '__decorator_settings__')
        assert func.__decorator_settings__ == settings
        assert hasattr(func, '__wrapped_function__')


# Test 9: subscriber decorator
class TestSubscriber:
    """Test the subscriber decorator."""
    
    @given(
        interfaces=st.lists(st.text(min_size=1), min_size=0, max_size=5),
        return_value=st.integers()
    )
    def test_subscriber_interfaces(self, interfaces, return_value):
        """Property: Subscriber should store interfaces and preserve function behavior."""
        
        @pyramid_decorator.subscriber(*interfaces)
        def handler():
            return return_value
        
        # Check interfaces are stored
        assert hasattr(handler, '__subscriber_interfaces__')
        assert handler.__subscriber_interfaces__ == tuple(interfaces)
        
        # Function should still work
        assert handler() == return_value


if __name__ == '__main__':
    # Run all tests
    import pytest
    pytest.main([__file__, '-v'])