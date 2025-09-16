import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, settings, example

# Import the modules we're testing
from pyramid.scripts.common import parse_vars
from pyramid.scripts.proutes import _get_pattern, _get_request_methods


# Edge case tests for parse_vars
def test_parse_vars_empty_key():
    """Test what happens with an empty key"""
    args = ['=value']
    result = parse_vars(args)
    assert result[''] == 'value'
    
    
def test_parse_vars_empty_value():
    """Test what happens with an empty value"""
    args = ['key=']
    result = parse_vars(args)
    assert result['key'] == ''
    

def test_parse_vars_duplicate_keys():
    """Test what happens with duplicate keys"""
    args = ['key=value1', 'key=value2']
    result = parse_vars(args)
    # The last value should win
    assert result['key'] == 'value2'
    assert len(result) == 1


def test_parse_vars_special_characters():
    """Test various special characters in keys and values"""
    test_cases = [
        ['key with spaces=value'],
        ['key\twith\ttabs=value'],
        ['key\nwith\nnewlines=value'],
        ['key=value=with=equals'],
        ['🦄=🦄'],
        ['key=value with spaces'],
        ['key='],
        ['=value'],
        ['=='],
        ['==='],
    ]
    
    for args in test_cases:
        result = parse_vars(args)
        key, value = args[0].split('=', 1)
        assert result[key] == value


# Test _get_pattern with special cases
def test_get_pattern_empty_string():
    """Test with empty pattern"""
    from pyramid.scripts.proutes import _get_pattern
    
    class MockRoute:
        def __init__(self, pattern):
            self.pattern = pattern
    
    route = MockRoute('')
    result = _get_pattern(route)
    assert result == '/'


def test_get_pattern_multiple_slashes():
    """Test with multiple leading slashes"""
    from pyramid.scripts.proutes import _get_pattern
    
    class MockRoute:
        def __init__(self, pattern):
            self.pattern = pattern
    
    route = MockRoute('//path')
    result = _get_pattern(route)
    assert result == '//path'  # Should preserve multiple slashes
    
    route = MockRoute('///path')
    result = _get_pattern(route)
    assert result == '///path'


# Test _get_request_methods edge cases
def test_get_request_methods_none_none():
    """Test with both None"""
    result = _get_request_methods(None, set())
    assert result == '*'


def test_get_request_methods_exclusion_only():
    """Test with only exclusions in view methods"""
    result = _get_request_methods(None, {'!GET'})
    assert '!GET' in result
    assert '*' in result


def test_get_request_methods_conflicting_exclusions():
    """Test when view has both a method and its exclusion"""
    # This is an edge case - what happens if view_methods has both 'GET' and '!GET'?
    result = _get_request_methods(None, {'GET', '!GET'})
    # The exclusion should be removed from the set
    assert 'GET' in result or result == '<route mismatch>'


def test_get_request_methods_empty_route_nonempty_view():
    """Test empty route methods with non-empty view methods"""
    result = _get_request_methods(set(), {'GET', 'POST'})
    assert result == '<route mismatch>'
    

def test_get_request_methods_nonempty_route_empty_view():
    """Test non-empty route methods with empty view methods"""
    result = _get_request_methods({'GET', 'POST'}, set())
    assert result == 'GET,POST'


# More complex scenarios
@given(
    st.lists(
        st.text(alphabet=st.characters(blacklist_characters='\x00'), min_size=1),
        min_size=0,
        max_size=100
    )
)
@settings(max_examples=500)
def test_parse_vars_with_many_equals(values):
    """Test parse_vars with values containing many equals signs"""
    # Create args with multiple equals signs in values
    args = []
    expected = {}
    for i, value in enumerate(values):
        key = f'key{i}'
        arg = f'{key}={value}'
        args.append(arg)
        expected[key] = value
    
    result = parse_vars(args)
    assert result == expected


@given(st.text(alphabet=st.characters(blacklist_characters='\x00')))
@settings(max_examples=500)
def test_get_pattern_unicode_and_special_chars(pattern):
    """Test _get_pattern with unicode and special characters"""
    from pyramid.scripts.proutes import _get_pattern
    
    class MockRoute:
        def __init__(self, pattern):
            self.pattern = pattern
    
    route = MockRoute(pattern)
    result = _get_pattern(route)
    
    # Should always start with /
    assert result.startswith('/')
    
    # If original started with /, should be unchanged
    if pattern.startswith('/'):
        assert result == pattern
    else:
        assert result == '/' + pattern