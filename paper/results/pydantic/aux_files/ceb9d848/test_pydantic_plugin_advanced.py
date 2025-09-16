import functools
import os
import sys
import warnings
from typing import Any
from unittest.mock import Mock, patch

import pytest
from hypothesis import assume, given, settings, strategies as st
from pydantic_core import ValidationError

import pydantic.plugin._loader as loader
import pydantic.plugin._schema_validator as validator
from pydantic.plugin import SchemaTypePath


class TestGetPluginsAdvanced:
    """Test the get_plugins function for plugin loading edge cases."""
    
    @given(st.sampled_from(['__all__', '1', 'true', 'false', '', None]))
    def test_get_plugins_environment_variable_handling(self, env_value):
        """Property: get_plugins should respect PYDANTIC_DISABLE_PLUGINS environment variable."""
        # Reset the global state
        loader._plugins = None
        loader._loading_plugins = False
        
        if env_value is not None:
            os.environ['PYDANTIC_DISABLE_PLUGINS'] = env_value
        elif 'PYDANTIC_DISABLE_PLUGINS' in os.environ:
            del os.environ['PYDANTIC_DISABLE_PLUGINS']
        
        try:
            plugins = list(loader.get_plugins())
            
            # When plugins are disabled, should return empty
            if env_value in ('__all__', '1', 'true'):
                assert plugins == []
            # Otherwise, it depends on what's installed
            # We can't assert much without mocking importlib_metadata
        finally:
            # Clean up
            if 'PYDANTIC_DISABLE_PLUGINS' in os.environ:
                del os.environ['PYDANTIC_DISABLE_PLUGINS']
            loader._plugins = None
            loader._loading_plugins = False
    
    def test_get_plugins_recursive_loading_protection(self):
        """Property: get_plugins should prevent recursive loading."""
        # Reset state
        loader._plugins = None
        loader._loading_plugins = False
        
        # Simulate recursive loading
        loader._loading_plugins = True
        
        plugins = list(loader.get_plugins())
        
        # Should return empty tuple when already loading
        assert plugins == []
        
        # Reset state
        loader._loading_plugins = False
    
    def test_get_plugins_caching(self):
        """Property: get_plugins should cache results after first call."""
        # Reset state
        loader._plugins = None
        loader._loading_plugins = False
        
        # Disable plugins to get predictable behavior
        os.environ['PYDANTIC_DISABLE_PLUGINS'] = '__all__'
        
        try:
            # First call
            plugins1 = list(loader.get_plugins())
            
            # State should be cached
            assert loader._plugins is not None
            
            # Second call should return same result
            plugins2 = list(loader.get_plugins())
            
            assert plugins1 == plugins2
            
            # Both should be empty since plugins are disabled
            assert plugins1 == []
            assert plugins2 == []
        finally:
            if 'PYDANTIC_DISABLE_PLUGINS' in os.environ:
                del os.environ['PYDANTIC_DISABLE_PLUGINS']
            loader._plugins = None
            loader._loading_plugins = False


class TestBuildWrapperEdgeCases:
    """Test edge cases in build_wrapper."""
    
    @given(st.text(min_size=1))
    def test_build_wrapper_validation_error_propagation(self, error_message):
        """Property: build_wrapper should properly propagate ValidationError."""
        error_handled = []
        
        class ErrorHandler:
            def on_error(self, error):
                error_handled.append(error)
        
        ErrorHandler.on_error.__module__ = 'test_module'
        
        def func():
            from pydantic_core import ErrorDetails
            raise ValidationError.from_exception_data(
                'test', 
                [ErrorDetails(type='value_error', loc=(), msg=error_message, input=None)]
            )
        
        wrapped = validator.build_wrapper(func, [ErrorHandler()])
        
        with pytest.raises(ValidationError) as exc_info:
            wrapped()
        
        # Handler should have been called
        assert len(error_handled) == 1
        assert isinstance(error_handled[0], ValidationError)
        
        # Error should be propagated unchanged
        assert str(exc_info.value).find(error_message) >= 0
    
    @given(st.text(min_size=1))
    def test_build_wrapper_generic_exception_propagation(self, error_message):
        """Property: build_wrapper should properly handle generic exceptions."""
        exception_handled = []
        
        class ExceptionHandler:
            def on_exception(self, exception):
                exception_handled.append(exception)
        
        ExceptionHandler.on_exception.__module__ = 'test_module'
        
        def func():
            raise ValueError(error_message)
        
        wrapped = validator.build_wrapper(func, [ExceptionHandler()])
        
        with pytest.raises(ValueError) as exc_info:
            wrapped()
        
        # Handler should have been called
        assert len(exception_handled) == 1
        assert isinstance(exception_handled[0], ValueError)
        assert str(exception_handled[0]) == error_message
        
        # Exception should be propagated unchanged
        assert str(exc_info.value) == error_message
    
    @given(st.lists(st.integers(), min_size=0, max_size=10))
    def test_build_wrapper_multiple_handlers(self, handler_count):
        """Property: build_wrapper should handle multiple handlers correctly."""
        call_counts = {'on_enter': 0, 'on_success': 0}
        
        handlers = []
        for i in range(len(handler_count)):
            class Handler:
                def on_enter(self, *args, **kwargs):
                    call_counts['on_enter'] += 1
                
                def on_success(self, result):
                    call_counts['on_success'] += 1
            
            Handler.on_enter.__module__ = f'test_module_{i}'
            Handler.on_success.__module__ = f'test_module_{i}'
            handlers.append(Handler())
        
        def func(x):
            return x * 2
        
        wrapped = validator.build_wrapper(func, handlers)
        
        result = wrapped(5)
        assert result == 10
        
        # Each handler should be called exactly once
        assert call_counts['on_enter'] == len(handler_count)
        assert call_counts['on_success'] == len(handler_count)


class TestSchemaTypePathCornerCases:
    """Test corner cases for SchemaTypePath."""
    
    @given(st.text())
    def test_schema_type_path_empty_strings(self, text):
        """Property: SchemaTypePath should handle empty strings."""
        # One empty, one not
        path1 = SchemaTypePath(module='', name=text)
        assert path1.module == ''
        assert path1.name == text
        
        path2 = SchemaTypePath(module=text, name='')
        assert path2.module == text
        assert path2.name == ''
        
        # Both empty
        path3 = SchemaTypePath(module='', name='')
        assert path3.module == ''
        assert path3.name == ''
        assert len(path3) == 2
    
    @given(st.text(min_size=1))
    def test_schema_type_path_same_values(self, value):
        """Property: SchemaTypePath should handle same module and name correctly."""
        path = SchemaTypePath(module=value, name=value)
        
        assert path.module == value
        assert path.name == value
        assert path[0] == value
        assert path[1] == value
        
        # Count should be 2 when both fields have same value
        assert path.count(value) == 2
        
        # Index should find first occurrence
        assert path.index(value) == 0
    
    @given(
        st.text(alphabet=st.characters(blacklist_categories=['Cs']), min_size=1),
        st.text(alphabet=st.characters(blacklist_categories=['Cs']), min_size=1)
    )
    def test_schema_type_path_special_characters(self, module, name):
        """Property: SchemaTypePath should handle special characters."""
        path = SchemaTypePath(module=module, name=name)
        
        assert path.module == module
        assert path.name == name
        
        # Should be hashable even with special characters
        hash_value = hash(path)
        assert isinstance(hash_value, int)
        
        # Should be comparable
        path2 = SchemaTypePath(module=module, name=name)
        assert path == path2
        assert hash(path) == hash(path2)