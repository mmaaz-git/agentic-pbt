"""Final property tests for Flask focusing on request/response cycle"""

from hypothesis import given, strategies as st, assume, settings
import flask
from flask import Flask, json, Response, Config, Request
from werkzeug.test import EnvironBuilder
from werkzeug.datastructures import Headers
import json as std_json


# Test werkzeug Request with various methods
@given(
    method=st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']),
    path=st.text(min_size=1, max_size=100).filter(lambda x: not any(c in x for c in ['\n', '\r', '\0'])),
    query_string=st.text(max_size=100).filter(lambda x: not any(c in x for c in ['\n', '\r', '\0']))
)
def test_request_construction(method, path, query_string):
    """Test Request object construction with various inputs"""
    # Ensure path starts with /
    if not path.startswith('/'):
        path = '/' + path
    
    builder = EnvironBuilder(method=method, path=path, query_string=query_string)
    env = builder.get_environ()
    
    request = Request(env)
    
    # Properties that should hold
    assert request.method == method
    assert path in request.path or request.path == path
    if query_string:
        assert request.query_string.decode('utf-8') == query_string or query_string in request.query_string.decode('utf-8')


# Test Flask app config inheritance
@given(
    parent_config=st.dictionaries(
        st.sampled_from(['DEBUG', 'TESTING', 'SECRET_KEY', 'DATABASE_URL']),
        st.one_of(st.integers(), st.text(max_size=50), st.booleans()),
        min_size=1,
        max_size=4
    ),
    child_config=st.dictionaries(
        st.sampled_from(['DEBUG', 'TESTING', 'API_KEY', 'PORT']),
        st.one_of(st.integers(), st.text(max_size=50), st.booleans()),
        max_size=3
    )
)
def test_config_inheritance(parent_config, child_config):
    """Test Config inheritance and override behavior"""
    config = Config('.')
    
    # Set parent config
    config.from_mapping(parent_config)
    
    # Override with child config
    config.from_mapping(child_config)
    
    # Child values should override parent
    for key in child_config:
        assert config[key] == child_config[key]
    
    # Parent values not in child should remain
    for key in parent_config:
        if key not in child_config:
            assert config[key] == parent_config[key]


# Test JSON encoder with custom objects
class CustomObject:
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return f"CustomObject({self.value})"


@given(
    custom_values=st.lists(st.integers(), min_size=1, max_size=10)
)
def test_json_custom_objects(custom_values):
    """Test Flask JSON with custom objects"""
    objects = [CustomObject(v) for v in custom_values]
    
    try:
        # Flask JSON should fail on custom objects by default
        encoded = json.dumps({"objects": objects})
        # If it succeeds, it might have used str() or repr()
        decoded = json.loads(encoded)
        # The decoded version won't match the original objects
    except TypeError:
        # Expected - can't serialize custom objects
        pass


# Test Response with large data
@given(
    large_data=st.binary(min_size=1024*1024, max_size=2*1024*1024)  # 1-2 MB
)
@settings(max_examples=5)
def test_response_large_data(large_data):
    """Test Response with large binary data"""
    response = Response(large_data)
    
    # Data should be preserved
    assert response.get_data() == large_data
    assert len(response.get_data()) == len(large_data)


# Test Config keys() and values() consistency
@given(
    config_data=st.dictionaries(
        st.sampled_from(['KEY1', 'KEY2', 'KEY3', 'KEY4', 'KEY5']),
        st.one_of(st.integers(), st.text(max_size=50)),
        min_size=1,
        max_size=5
    )
)
def test_config_keys_values_consistency(config_data):
    """Test that Config maintains consistency between keys() and values()"""
    config = Config('.')
    config.from_mapping(config_data)
    
    keys_list = list(config.keys())
    values_list = list(config.values())
    
    # Should have same length
    assert len(keys_list) == len(values_list)
    assert len(keys_list) == len(config_data)
    
    # Each key should map to its value
    for i, key in enumerate(keys_list):
        if key in config_data:  # Only check our added keys
            assert config[key] in values_list


# Test Headers case insensitivity
@given(
    header_name=st.text(min_size=1, max_size=50).filter(
        lambda x: not any(c in x for c in ['\n', '\r', ':', '\0'])
    ),
    header_value=st.text(max_size=100).filter(
        lambda x: not any(c in x for c in ['\n', '\r', '\0'])
    )
)
def test_headers_case_insensitivity(header_name, header_value):
    """Test that Headers are case-insensitive for names"""
    headers = Headers()
    headers[header_name] = header_value
    
    # Should be retrievable with different cases
    if header_name.lower() != header_name:
        assert headers.get(header_name.lower()) == header_value or headers.get(header_name.upper()) == header_value
    
    # Original case should work
    assert headers.get(header_name) == header_value


# Test Config clear operation
@given(
    initial_data=st.dictionaries(
        st.sampled_from(['KEY1', 'KEY2', 'KEY3']),
        st.integers(),
        min_size=1,
        max_size=3
    )
)
def test_config_clear(initial_data):
    """Test Config.clear() operation"""
    config = Config('.')
    config.from_mapping(initial_data)
    
    # Verify data is there
    assert len(config) == len(initial_data)
    
    # Clear the config
    config.clear()
    
    # Should be empty
    assert len(config) == 0
    for key in initial_data:
        assert key not in config