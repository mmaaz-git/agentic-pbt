import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import math
import pytest
from hypothesis import assume, given, strategies as st, settings, HealthCheck

# Import the modules we're testing
from pyramid.scripts.common import parse_vars
from pyramid.scripts.proutes import _get_pattern, _get_request_methods


class MockRoute:
    def __init__(self, pattern):
        self.pattern = pattern
        

# Test parse_vars function
@given(st.dictionaries(
    st.text(min_size=1).filter(lambda x: '=' not in x),
    st.text(),
    min_size=0,
    max_size=10
))
def test_parse_vars_round_trip(input_dict):
    """Test that parse_vars correctly parses valid variable assignments"""
    # Create input in the format parse_vars expects
    args = [f"{key}={value}" for key, value in input_dict.items()]
    
    # Parse the variables
    result = parse_vars(args)
    
    # Check that we get the expected dictionary back
    assert result == input_dict
    assert isinstance(result, dict)


@given(st.lists(
    st.text(min_size=1).filter(lambda x: '=' in x),
    min_size=0,
    max_size=20
))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_parse_vars_preserves_values_after_first_equals(args):
    """Test that parse_vars correctly handles multiple '=' in values"""
    result = parse_vars(args)
    
    # Check each arg was parsed correctly
    for arg in args:
        if '=' in arg:
            name, value = arg.split('=', 1)
            assert result[name] == value
            # Value should preserve all content after the first '='
            if '=' in value:
                assert '=' in result[name]


@given(st.lists(
    st.text(min_size=1).filter(lambda x: '=' not in x),
    min_size=1,
    max_size=5
))
def test_parse_vars_invalid_input_raises(args):
    """Test that parse_vars raises ValueError for invalid input without '='"""
    with pytest.raises(ValueError) as exc_info:
        parse_vars(args)
    assert 'invalid (no "=")' in str(exc_info.value)


# Test _get_pattern function
@given(st.text(min_size=1))
def test_get_pattern_always_starts_with_slash(pattern_text):
    """Test that _get_pattern ensures result always starts with '/'"""
    route = MockRoute(pattern_text)
    result = _get_pattern(route)
    
    assert result.startswith('/')
    
    # If original started with '/', it should be unchanged
    if pattern_text.startswith('/'):
        assert result == pattern_text
    else:
        assert result == '/' + pattern_text


@given(st.text(min_size=0))
def test_get_pattern_idempotent(pattern_text):
    """Test that applying _get_pattern twice gives the same result"""
    route1 = MockRoute(pattern_text)
    result1 = _get_pattern(route1)
    
    route2 = MockRoute(result1)
    result2 = _get_pattern(route2)
    
    assert result1 == result2


# Test _get_request_methods with various combinations
@given(
    route_methods=st.one_of(
        st.none(),
        st.sets(st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH']), min_size=0, max_size=7)
    ),
    view_methods=st.sets(
        st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH', '!GET', '!POST']),
        min_size=0,
        max_size=9
    )
)
def test_get_request_methods_handles_various_inputs(route_methods, view_methods):
    """Test _get_request_methods with various method combinations"""
    result = _get_request_methods(route_methods, view_methods)
    
    # Result should be a string or the special '<route mismatch>' value
    assert isinstance(result, str)
    
    # If both are None/empty, should return '*'
    if route_methods is None and len(view_methods) == 0:
        assert result == '*'
    
    # If result is not a mismatch, it should contain valid method names
    if result != '<route mismatch>':
        if result != '*':
            # Should be comma-separated methods
            if ',' in result:
                methods = result.split(',')
                for method in methods:
                    # Each method should be non-empty
                    assert len(method.strip()) > 0


@given(
    methods=st.sets(st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']), min_size=1, max_size=4)
)
def test_get_request_methods_intersection(methods):
    """Test that intersection logic works correctly"""
    # When both route and view have the same methods
    route_methods = methods
    view_methods = methods.copy()
    
    result = _get_request_methods(route_methods, view_methods)
    
    # Should get back the same methods
    if result != '<route mismatch>':
        result_methods = set(result.split(','))
        assert result_methods == methods


@given(st.sets(st.sampled_from(['GET', 'POST', 'PUT', 'DELETE']), min_size=1, max_size=4))
def test_get_request_methods_empty_intersection(methods):
    """Test behavior when route and view methods have no overlap"""
    route_methods = methods
    # Create disjoint set
    all_methods = {'GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS', 'PATCH'}
    view_methods = all_methods - methods
    
    if len(view_methods) > 0:
        result = _get_request_methods(route_methods, view_methods)
        # Should indicate a mismatch when there's no intersection
        assert result == '<route mismatch>'


# Test exclusion logic
def test_get_request_methods_exclusion():
    """Test that exclusion with '!' prefix works correctly"""
    # Test exclusion from view methods
    route_methods = None
    view_methods = {'GET', 'POST', '!DELETE'}
    
    result = _get_request_methods(route_methods, view_methods)
    
    # Should have GET and POST but not DELETE
    assert 'GET' in result
    assert 'POST' in result
    assert 'DELETE' not in result or '!DELETE' in result
    
    
def test_get_request_methods_any_with_exclusion():
    """Test ANY_KEY ('*') with exclusions"""
    route_methods = None
    view_methods = {'!GET', '!POST'}
    
    result = _get_request_methods(route_methods, view_methods)
    
    # Should return * with exclusions listed
    assert '!GET' in result
    assert '!POST' in result