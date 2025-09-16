#!/usr/bin/env python3
"""Property-based tests for pyramid.viewderivers module."""

import inspect
from hypothesis import given, strategies as st, assume, settings
import pyramid.viewderivers as vd
from pyramid.exceptions import ConfigurationError


# Test preserve_view_attrs properties
@given(st.text())
def test_preserve_view_attrs_none_view(wrapper_name):
    """When view is None, should return wrapper unchanged."""
    def wrapper():
        pass
    wrapper.__name__ = wrapper_name
    
    result = vd.preserve_view_attrs(None, wrapper)
    assert result is wrapper


@given(st.text(), st.text())
def test_preserve_view_attrs_same_view_wrapper(name, doc):
    """When wrapper is view, should return view unchanged."""
    def view():
        pass
    view.__name__ = name
    view.__doc__ = doc
    
    result = vd.preserve_view_attrs(view, view)
    assert result is view


@given(st.text(), st.text(), st.text(), st.text())
def test_preserve_view_attrs_copies_attributes(view_name, view_doc, wrapper_name, module_name):
    """Should copy specific attributes from view to wrapper."""
    def view():
        pass
    def wrapper():
        pass
    
    # Set up view attributes
    view.__name__ = view_name
    view.__doc__ = view_doc
    view.__module__ = module_name
    wrapper.__name__ = wrapper_name
    
    result = vd.preserve_view_attrs(view, wrapper)
    
    # Check that attributes were copied
    assert result.__module__ == module_name
    assert result.__doc__ == view_doc
    assert result.__name__ == view_name
    assert result.__wraps__ is view
    assert result.__original_view__ is view


@given(st.text())
def test_preserve_view_attrs_handles_missing_name(doc):
    """Should handle views without __name__ attribute."""
    class ViewWithoutName:
        pass
    
    view = ViewWithoutName()
    view.__doc__ = doc
    view.__module__ = 'test.module'
    
    def wrapper():
        pass
    
    result = vd.preserve_view_attrs(view, wrapper)
    
    # Should use repr(view) when __name__ is missing
    assert result.__name__ == repr(view)
    assert result.__doc__ == doc


# Test view_description properties
@given(st.text())
def test_view_description_with_text_attr(text):
    """Should return __text__ attribute if it exists."""
    class ViewWithText:
        def __init__(self):
            self.__text__ = text
    
    view = ViewWithText()
    result = vd.view_description(view)
    assert result == text


def test_view_description_without_text_attr():
    """Should fall back to object_description when __text__ missing."""
    def sample_view():
        pass
    
    result = vd.view_description(sample_view)
    # Should contain function description
    assert 'function' in result or 'sample_view' in result


# Test DefaultViewMapper properties
def test_default_view_mapper_unbound_method_error():
    """Should raise ConfigurationError for unbound methods without attr."""
    mapper = vd.DefaultViewMapper()
    
    class MyClass:
        def my_method(self):
            pass
    
    # Get unbound method
    unbound = MyClass.my_method
    
    # Should raise ConfigurationError
    try:
        mapper(unbound)
        assert False, "Should have raised ConfigurationError"
    except ConfigurationError as e:
        assert "Unbound method calls are not supported" in str(e)


@given(st.text(min_size=1))
def test_default_view_mapper_class_sets_text(attr_name):
    """Mapped class views should have __text__ attribute."""
    mapper = vd.DefaultViewMapper(attr=attr_name)
    
    class TestView:
        def __init__(self, context, request):
            self.context = context
            self.request = request
        
        def custom_attr(self):
            return "response"
    
    # Add the custom attribute
    setattr(TestView, attr_name, lambda self: "response")
    
    mapped = mapper(TestView)
    
    # Should have __text__ attribute
    assert hasattr(mapped, '__text__')
    assert attr_name in mapped.__text__


# Test http_cached_view tuple parsing
def test_http_cached_view_invalid_tuple():
    """Should raise ConfigurationError for invalid cache tuple format."""
    
    class MockInfo:
        def __init__(self):
            self.settings = {}
            self.options = {'http_cache': (300, 'invalid', 'extra')}  # Invalid tuple
    
    def dummy_view(context, request):
        return "response"
    
    info = MockInfo()
    
    try:
        vd.http_cached_view(dummy_view, info)
        assert False, "Should have raised ConfigurationError"
    except ConfigurationError as e:
        assert "must be in the form (seconds, options)" in str(e)


@given(st.integers(min_value=0, max_value=86400))
def test_http_cached_view_with_integer(seconds):
    """Should handle integer cache seconds."""
    
    class MockInfo:
        def __init__(self):
            self.settings = {}
            self.options = {'http_cache': seconds}
    
    def dummy_view(context, request):
        from pyramid.response import Response
        return Response("test")
    
    info = MockInfo()
    wrapped = vd.http_cached_view(dummy_view, info)
    
    # Should return a wrapper function if seconds is not None
    if seconds is not None:
        assert wrapped != dummy_view
        assert callable(wrapped)


@given(st.integers(min_value=0, max_value=86400))
def test_http_cached_view_with_tuple(seconds):
    """Should handle (seconds, options) tuple format."""
    
    class MockInfo:
        def __init__(self):
            self.settings = {}
            self.options = {'http_cache': (seconds, {'public': True})}
    
    def dummy_view(context, request):
        from pyramid.response import Response
        return Response("test")
    
    info = MockInfo()
    wrapped = vd.http_cached_view(dummy_view, info)
    
    # Should return a wrapper function
    assert wrapped != dummy_view
    assert callable(wrapped)


# Test requestonly function
@given(st.text(min_size=1))
def test_requestonly_with_single_arg_function(arg_name):
    """Should correctly identify functions taking one argument."""
    # Function that takes exactly one argument
    exec(f"def single_arg_func({arg_name}): pass", globals())
    func = globals()['single_arg_func']
    
    result = vd.requestonly(func, argname=arg_name)
    assert result == True
    
    # Clean up
    del globals()['single_arg_func']


def test_requestonly_with_multiple_args():
    """Should return False for functions with multiple required args."""
    def multi_arg_func(request, context):
        pass
    
    result = vd.requestonly(multi_arg_func, argname='request')
    assert result == False


def test_requestonly_with_class():
    """Should check __init__ method for classes."""
    class SingleArgClass:
        def __init__(self, request):
            self.request = request
    
    result = vd.requestonly(SingleArgClass, argname='request')
    assert result == True
    
    class MultiArgClass:
        def __init__(self, context, request):
            self.context = context
            self.request = request
    
    result = vd.requestonly(MultiArgClass, argname='request')
    assert result == False