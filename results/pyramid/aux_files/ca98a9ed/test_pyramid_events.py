"""Property-based tests for pyramid.events module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from pyramid.events import (
    BeforeRender, NewRequest, NewResponse, BeforeTraversal,
    ContextFound, ApplicationCreated, subscriber
)
from zope.interface import Interface
import pytest


# Test 1: BeforeRender dictionary behavior
@given(
    system_dict=st.dictionaries(
        st.text(min_size=1), 
        st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))
    ),
    rendering_val=st.one_of(st.none(), st.dictionaries(st.text(), st.text()))
)
def test_before_render_dict_behavior(system_dict, rendering_val):
    """BeforeRender should behave like a dictionary as documented"""
    event = BeforeRender(system_dict, rendering_val)
    
    # Should be a dict subclass
    assert isinstance(event, dict)
    
    # Should initialize with system dict values
    for key, value in system_dict.items():
        assert event[key] == value
    
    # Should preserve rendering_val
    assert event.rendering_val == rendering_val
    
    # Should support dict operations
    test_key = "test_key_unique_12345"
    test_value = "test_value"
    
    # __setitem__ should work
    event[test_key] = test_value
    assert event[test_key] == test_value
    
    # get should work
    assert event.get(test_key) == test_value
    assert event.get("nonexistent_key_99999", "default") == "default"
    
    # __contains__ should work
    assert test_key in event
    assert "nonexistent_key_99999" not in event
    
    # Should preserve dict equality semantics
    dict_copy = dict(event)
    assert dict_copy == dict(event)


# Test 2: Event class attribute preservation
@given(request_obj=st.dictionaries(st.text(), st.text()))
def test_new_request_preserves_request(request_obj):
    """NewRequest should preserve the request object passed to it"""
    event = NewRequest(request_obj)
    assert event.request is request_obj


@given(
    request_obj=st.dictionaries(st.text(), st.text()),
    response_obj=st.dictionaries(st.text(), st.text())
)
def test_new_response_preserves_attributes(request_obj, response_obj):
    """NewResponse should preserve both request and response objects"""
    event = NewResponse(request_obj, response_obj)
    assert event.request is request_obj
    assert event.response is response_obj


@given(app_obj=st.dictionaries(st.text(), st.text()))
def test_application_created_preserves_app(app_obj):
    """ApplicationCreated should preserve app object in both attributes"""
    event = ApplicationCreated(app_obj)
    assert event.app is app_obj
    assert event.object is app_obj  # backward compatibility attribute


# Test 3: subscriber decorator properties
@given(
    predicates=st.dictionaries(
        st.sampled_from(['predicate1', 'predicate2', 'predicate3']),
        st.one_of(st.text(), st.integers(), st.booleans())
    )
)
def test_subscriber_preserves_predicates(predicates):
    """subscriber decorator should preserve predicates passed to it"""
    # Avoid reserved predicates
    assume('_depth' not in predicates)
    assume('_category' not in predicates)
    
    decorator = subscriber(**predicates)
    assert decorator.predicates == predicates


@given(
    num_interfaces=st.integers(min_value=0, max_value=5),
    depth=st.integers(min_value=0, max_value=10),
    category=st.text(min_size=1)
)
def test_subscriber_special_params(num_interfaces, depth, category):
    """subscriber should correctly handle _depth and _category parameters"""
    interfaces = [Interface for _ in range(num_interfaces)]
    predicates = {'_depth': depth, '_category': category}
    
    decorator = subscriber(*interfaces, **predicates)
    
    assert decorator.ifaces == tuple(interfaces)
    assert decorator.depth == depth
    assert decorator.category == category
    # These should be removed from predicates
    assert '_depth' not in decorator.predicates
    assert '_category' not in decorator.predicates


# Test 4: BeforeRender dictionary round-trip property
@given(
    initial_data=st.dictionaries(
        st.text(min_size=1), 
        st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))
    ),
    updates=st.lists(
        st.tuples(
            st.text(min_size=1),
            st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))
        ),
        max_size=10
    )
)
def test_before_render_update_retrieval(initial_data, updates):
    """Values set in BeforeRender should be retrievable"""
    event = BeforeRender(initial_data)
    
    # Apply all updates
    for key, value in updates:
        event[key] = value
    
    # Verify all updates are retrievable
    for key, value in updates:
        assert event[key] == value
        assert event.get(key) == value
        assert key in event


# Test 5: Event class identity properties
@given(request_obj=st.dictionaries(st.text(), st.text()))
def test_event_classes_preserve_identity(request_obj):
    """Event classes should preserve object identity, not copy"""
    # Test NewRequest
    nr = NewRequest(request_obj)
    assert nr.request is request_obj
    request_obj['modified'] = 'value'
    assert nr.request['modified'] == 'value'
    
    # Test BeforeTraversal
    bt = BeforeTraversal(request_obj)
    assert bt.request is request_obj
    
    # Test ContextFound
    cf = ContextFound(request_obj)
    assert cf.request is request_obj


# Test 6: BeforeRender overwrite behavior
@given(
    system_dict=st.dictionaries(
        st.text(min_size=1),
        st.text(),
        min_size=1
    ),
    key=st.text(min_size=1),
    old_value=st.text(),
    new_value=st.text()
)
def test_before_render_overwrite(system_dict, key, old_value, new_value):
    """BeforeRender should allow overwriting existing keys as documented"""
    assume(old_value != new_value)
    system_dict[key] = old_value
    
    event = BeforeRender(system_dict)
    assert event[key] == old_value
    
    # Overwrite should work
    event[key] = new_value
    assert event[key] == new_value
    assert event.get(key) == new_value


# Test 7: subscriber decorator callable property
def test_subscriber_returns_wrapped_function():
    """subscriber decorator should return the original wrapped function"""
    def dummy_func():
        return "test"
    
    decorator = subscriber()
    wrapped = decorator(dummy_func)
    
    # Should return the same function
    assert wrapped is dummy_func
    assert wrapped() == "test"


# Test 8: BeforeRender inherits all dict methods
@given(
    data=st.dictionaries(
        st.text(min_size=1),
        st.integers(),
        min_size=1
    )
)
def test_before_render_dict_methods(data):
    """BeforeRender should support all standard dict methods"""
    event = BeforeRender(data)
    
    # keys() method
    assert set(event.keys()) == set(data.keys())
    
    # values() method - compare as lists after sorting
    assert sorted(event.values(), key=str) == sorted(data.values(), key=str)
    
    # items() method
    assert set(event.items()) == set(data.items())
    
    # len() function
    assert len(event) == len(data)
    
    # pop() method
    if data:
        key = next(iter(data))
        val = event.pop(key)
        assert val == data[key]
        assert key not in event