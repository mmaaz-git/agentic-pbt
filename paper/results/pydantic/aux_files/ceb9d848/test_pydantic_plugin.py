import functools
import sys
from typing import Any, Protocol
from unittest.mock import Mock

import pytest
from hypothesis import assume, given, strategies as st

import pydantic.plugin
from pydantic.plugin import SchemaTypePath
from pydantic.plugin._schema_validator import build_wrapper, filter_handlers


# Test filter_handlers function
class TestFilterHandlers:
    """Test the filter_handlers function that filters out unimplemented handler methods."""
    
    @given(st.text(min_size=1, max_size=100))
    def test_filter_handlers_missing_method(self, method_name):
        """Property: filter_handlers should return False for non-existent methods."""
        # Create a mock handler class with no methods
        class MockHandler:
            pass
        
        # Should return False for any non-existent method
        result = filter_handlers(MockHandler, method_name)
        assert result is False
    
    @given(st.text(min_size=1, max_size=100).filter(lambda x: x not in ['__class__', '__dict__']))
    def test_filter_handlers_protocol_method(self, method_name):
        """Property: filter_handlers should return False for methods from pydantic.plugin module."""
        # Create a mock handler with a method from pydantic.plugin module
        class MockHandler:
            pass
        
        # Add a method with __module__ set to 'pydantic.plugin'
        method = lambda self: None
        method.__module__ = 'pydantic.plugin'
        setattr(MockHandler, method_name, method)
        
        result = filter_handlers(MockHandler, method_name)
        assert result is False
    
    @given(
        st.text(min_size=1, max_size=100).filter(lambda x: x not in ['__class__', '__dict__']),
        st.text(min_size=1, max_size=100).filter(lambda x: x != 'pydantic.plugin')
    )
    def test_filter_handlers_custom_method(self, method_name, module_name):
        """Property: filter_handlers should return True for custom implemented methods."""
        # Create a mock handler with a custom method
        class MockHandler:
            pass
        
        # Add a method with a different module
        method = lambda self: None
        method.__module__ = module_name
        setattr(MockHandler, method_name, method)
        
        result = filter_handlers(MockHandler, method_name)
        assert result is True


# Test build_wrapper function
class TestBuildWrapper:
    """Test the build_wrapper function that wraps functions with event handlers."""
    
    @given(st.integers(), st.integers())
    def test_build_wrapper_no_handlers_preserves_function(self, a, b):
        """Property: build_wrapper with no handlers should return the original function."""
        def original_func(x, y):
            return x + y
        
        wrapped = build_wrapper(original_func, [])
        
        # The wrapped function should behave identically to the original
        assert wrapped(a, b) == original_func(a, b)
        assert wrapped(a, b) == a + b
    
    @given(st.lists(st.integers(), min_size=1, max_size=10))
    def test_build_wrapper_handlers_called_in_order(self, values):
        """Property: Event handlers should be called in correct order."""
        call_log = []
        
        class MockHandler:
            def on_enter(self, *args, **kwargs):
                call_log.append(('on_enter', args, kwargs))
            
            def on_success(self, result):
                call_log.append(('on_success', result))
        
        # Make filter_handlers accept our mock handler
        MockHandler.on_enter.__module__ = 'test_module'
        MockHandler.on_success.__module__ = 'test_module'
        
        def func(*args):
            call_log.append(('func', args))
            return sum(args)
        
        wrapped = build_wrapper(func, [MockHandler()])
        
        # Call the wrapped function
        result = wrapped(*values)
        
        # Verify correct order: on_enter -> func -> on_success
        assert len(call_log) == 3
        assert call_log[0][0] == 'on_enter'
        assert call_log[1][0] == 'func'
        assert call_log[2][0] == 'on_success'
        assert call_log[2][1] == sum(values)
        assert result == sum(values)
    
    @given(st.text(min_size=1, max_size=100))
    def test_build_wrapper_preserves_function_metadata(self, doc_string):
        """Property: build_wrapper should preserve function metadata."""
        def original_func(x):
            return x
        
        original_func.__doc__ = doc_string
        original_func.__name__ = 'test_func'
        
        wrapped = build_wrapper(original_func, [])
        
        # Wrapped function should preserve metadata
        assert wrapped.__doc__ == original_func.__doc__
        assert wrapped.__name__ == original_func.__name__


# Test SchemaTypePath named tuple
class TestSchemaTypePath:
    """Test the SchemaTypePath named tuple."""
    
    @given(st.text(min_size=1), st.text(min_size=1))
    def test_schema_type_path_immutability(self, module, name):
        """Property: SchemaTypePath should be immutable like a tuple."""
        path = SchemaTypePath(module=module, name=name)
        
        # Should be accessible by index
        assert path[0] == module
        assert path[1] == name
        
        # Should be accessible by name
        assert path.module == module
        assert path.name == name
        
        # Should not be modifiable
        with pytest.raises((TypeError, AttributeError)):
            path.module = 'new_module'
        
        with pytest.raises(TypeError):
            path[0] = 'new_module'
    
    @given(st.text(min_size=1), st.text(min_size=1))
    def test_schema_type_path_tuple_operations(self, module, name):
        """Property: SchemaTypePath should support standard tuple operations."""
        path = SchemaTypePath(module=module, name=name)
        
        # Count should work
        assert path.count(module) >= 1
        assert path.count(name) >= 1 if name != module else path.count(name) >= 2
        
        # Index should work
        assert path.index(module) == 0
        if name != module:
            assert path.index(name) == 1
        
        # Length should be 2
        assert len(path) == 2
        
        # Should be iterable
        items = list(path)
        assert items == [module, name]
    
    @given(st.text(min_size=1), st.text(min_size=1))
    def test_schema_type_path_equality(self, module, name):
        """Property: SchemaTypePath instances with same values should be equal."""
        path1 = SchemaTypePath(module=module, name=name)
        path2 = SchemaTypePath(module=module, name=name)
        path3 = SchemaTypePath(module=name, name=module)  # Swapped
        
        assert path1 == path2
        assert hash(path1) == hash(path2)
        
        if module != name:
            assert path1 != path3


# Test edge cases and interactions
class TestPluginInteractions:
    """Test interactions between plugin components."""
    
    @given(st.lists(st.sampled_from(['on_enter', 'on_success', 'on_error', 'on_exception']), min_size=0, max_size=4))
    def test_build_wrapper_with_selective_handlers(self, handler_methods):
        """Property: build_wrapper should work correctly with any subset of handler methods."""
        call_log = []
        
        class SelectiveHandler:
            pass
        
        # Add only selected handler methods
        for method_name in handler_methods:
            def make_handler(name):
                def handler(self, *args, **kwargs):
                    call_log.append(name)
                return handler
            
            handler = make_handler(method_name)
            handler.__module__ = 'test_module'
            setattr(SelectiveHandler, method_name, handler)
        
        def func(x):
            return x * 2
        
        wrapped = build_wrapper(func, [SelectiveHandler()])
        
        # Should not crash regardless of which handlers are present
        result = wrapped(5)
        assert result == 10
        
        # Only on_enter and on_success should be called for successful execution
        expected_calls = []
        if 'on_enter' in handler_methods:
            expected_calls.append('on_enter')
        if 'on_success' in handler_methods:
            expected_calls.append('on_success')
        
        assert call_log == expected_calls