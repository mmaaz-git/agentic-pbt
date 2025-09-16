import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.view as view
from pyramid.exceptions import ConfigurationError
from pyramid.httpexceptions import HTTPTemporaryRedirect, HTTPNotFound


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_view_config_preserves_function_identity(settings_dict):
    """Test that view_config decorator returns the wrapped function unchanged"""
    def dummy_func():
        return 42
    
    decorator = view.view_config(**settings_dict)
    wrapped = decorator(dummy_func)
    
    assert wrapped is dummy_func
    assert wrapped() == 42


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_view_config_for_parameter_aliasing(settings_dict):
    """Test that 'for_' parameter is aliased to 'context' when context is None"""
    assume('context' not in settings_dict)
    assume('for_' not in settings_dict)
    
    test_value = object()
    settings_dict['for_'] = test_value
    
    config = view.view_config(**settings_dict)
    
    assert config.context is test_value
    assert config.for_ is test_value


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_view_config_stores_settings(settings_dict):
    """Test that view_config stores all provided settings in __dict__"""
    config = view.view_config(**settings_dict)
    
    for key, value in settings_dict.items():
        assert hasattr(config, key)
        assert getattr(config, key) == value


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_view_defaults_decorator_stores_settings(settings_dict):
    """Test that view_defaults decorator stores settings in __view_defaults__"""
    class DummyClass:
        pass
    
    wrapped = view.view_defaults(**settings_dict)(DummyClass)
    
    assert wrapped is DummyClass
    assert hasattr(wrapped, '__view_defaults__')
    assert wrapped.__view_defaults__ == settings_dict


@given(st.text())
def test_exception_view_config_positional_context(exception_class_name):
    """Test that exception_view_config accepts context as positional argument"""
    class CustomException(Exception):
        pass
    
    config = view.exception_view_config(CustomException)
    assert config.context is CustomException


@given(st.text(), st.text())
def test_exception_view_config_rejects_extra_positional_args(arg1, arg2):
    """Test that exception_view_config raises ConfigurationError for extra positional args"""
    class CustomException(Exception):
        pass
    
    try:
        config = view.exception_view_config(CustomException, arg1, arg2)
        assert False, "Should have raised ConfigurationError"
    except ConfigurationError as e:
        assert 'unknown positional arguments' in str(e)


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_exception_view_config_keyword_context(settings_dict):
    """Test that exception_view_config accepts context as keyword argument"""
    class CustomException(Exception):
        pass
    
    settings_dict['context'] = CustomException
    config = view.exception_view_config(**settings_dict)
    assert config.context is CustomException


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_notfound_view_config_stores_settings(settings_dict):
    """Test that notfound_view_config stores all settings"""
    config = view.notfound_view_config(**settings_dict)
    
    for key, value in settings_dict.items():
        assert hasattr(config, key)
        assert getattr(config, key) == value


@given(st.dictionaries(st.text(min_size=1), st.text()))
def test_forbidden_view_config_stores_settings(settings_dict):
    """Test that forbidden_view_config stores all settings"""
    config = view.forbidden_view_config(**settings_dict)
    
    for key, value in settings_dict.items():
        assert hasattr(config, key)
        assert getattr(config, key) == value


@given(st.text(min_size=1).filter(lambda x: '/' not in x))
def test_append_slash_factory_path_handling(path_segment):
    """Test AppendSlashNotFoundViewFactory path construction"""
    class MockRequest:
        def __init__(self, path):
            self.path_info = path
            self.path = path
            self.query_string = ''
            self.registry = None
    
    class MockContext:
        pass
    
    factory = view.AppendSlashNotFoundViewFactory()
    request = MockRequest('/' + path_segment)
    context = MockContext()
    
    result = factory(context, request)
    
    assert isinstance(result, (HTTPNotFound, HTTPTemporaryRedirect, type(None))) or callable(result)


@given(st.text(min_size=1), st.text())
def test_append_slash_preserves_query_string(path_segment, query_string):
    """Test that AppendSlashNotFoundViewFactory preserves query strings in redirects"""
    assume('/' not in path_segment)
    assume('\x00' not in query_string)
    
    class MockRoute:
        def match(self, path):
            return {'match': 'data'} if path.endswith('/') else None
    
    class MockMapper:
        def get_routes(self):
            return [MockRoute()]
    
    class MockRegistry:
        def queryUtility(self, interface):
            from pyramid.interfaces import IRoutesMapper
            if interface == IRoutesMapper:
                return MockMapper()
            return None
    
    class MockRequest:
        def __init__(self, path, qs):
            self.path_info = path
            self.path = path
            self.query_string = qs
            self.registry = MockRegistry()
    
    class MockContext:
        pass
    
    factory = view.AppendSlashNotFoundViewFactory()
    request = MockRequest('/' + path_segment, query_string)
    context = MockContext()
    
    result = factory(context, request)
    
    if isinstance(result, HTTPTemporaryRedirect):
        if query_string:
            assert result.location == '/' + path_segment + '/' + '?' + query_string
        else:
            assert result.location == '/' + path_segment + '/'


@given(st.lists(st.text(min_size=1), min_size=1, max_size=5))
def test_view_config_with_different_depths(text_list):
    """Test view_config with _depth parameter"""
    settings = {key: key for key in text_list}
    settings['_depth'] = 0
    
    config = view.view_config(**settings)
    
    for key in text_list:
        assert hasattr(config, key)
        assert getattr(config, key) == key


@given(st.text(min_size=1))
def test_view_config_category_parameter(category_name):
    """Test view_config with _category parameter"""
    config = view.view_config(_category=category_name)
    
    assert hasattr(config, '_category')
    assert config._category == category_name
    
    def dummy():
        pass
    
    wrapped = config(dummy)
    assert wrapped is dummy