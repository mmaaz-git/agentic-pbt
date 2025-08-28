"""Property-based tests for Flask using Hypothesis"""

import tempfile
import os
from hypothesis import given, strategies as st, assume, settings
import flask
from flask import json, Response, Config
import json as std_json


# Test 1: Flask Config maintains dict invariants
@given(
    initial_data=st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isupper()),
        st.one_of(
            st.integers(),
            st.text(),
            st.booleans(),
            st.none(),
            st.lists(st.integers(), max_size=10)
        )
    ),
    key_to_update=st.text(min_size=1, max_size=50).filter(lambda x: x.isupper()),
    value_to_update=st.one_of(st.integers(), st.text(), st.booleans())
)
def test_config_dict_invariants(initial_data, key_to_update, value_to_update):
    """Test that Flask Config behaves like a dict with special handling for uppercase keys"""
    config = Config('.')
    
    # Property 1: from_mapping should preserve all mappings
    config.from_mapping(initial_data)
    for key, value in initial_data.items():
        assert config[key] == value, f"Config lost mapping for {key}"
    
    # Property 2: len should match number of keys
    assert len(config) == len(initial_data)
    
    # Property 3: Update should work like dict update
    config[key_to_update] = value_to_update
    assert config[key_to_update] == value_to_update
    
    # Property 4: Keys should be retrievable
    assert key_to_update in config
    assert set(initial_data.keys()) <= set(config.keys())


# Test 2: Flask JSON round-trip property
@given(
    data=st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
            st.text(max_size=1000)
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=50),
            st.dictionaries(
                st.text(min_size=1, max_size=100),
                children,
                max_size=50
            )
        ),
        max_leaves=1000
    )
)
def test_json_round_trip(data):
    """Test that Flask's JSON can round-trip data structures"""
    # Flask JSON should round-trip valid JSON data
    encoded = json.dumps(data)
    decoded = json.loads(encoded)
    
    # Property: decode(encode(x)) == x for JSON-serializable data
    assert decoded == data, f"Round-trip failed for {data}"
    
    # Property: Flask JSON should be compatible with standard JSON
    std_encoded = std_json.dumps(data)
    flask_decoded_from_std = json.loads(std_encoded)
    assert flask_decoded_from_std == data


# Test 3: Flask Response status codes
@given(
    status_code=st.integers(min_value=100, max_value=599),
    response_data=st.text(max_size=1000)
)
def test_response_status_codes(status_code, response_data):
    """Test that Flask Response correctly handles status codes"""
    # Create response with status code
    response = Response(response_data, status=status_code)
    
    # Property: Status code should be preserved
    assert response.status_code == status_code
    
    # Property: Status string should reflect the code
    assert response.status.startswith(str(status_code))
    
    # Property: Response data should be preserved
    assert response.get_data(as_text=True) == response_data


# Test 4: Config from_object property
class ConfigObject:
    """Helper class for testing from_object"""
    pass

@given(
    config_data=st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isupper() and x.isidentifier()),
        st.one_of(
            st.integers(),
            st.text(max_size=100),
            st.booleans(),
            st.none()
        ),
        min_size=1,
        max_size=20
    )
)
def test_config_from_object(config_data):
    """Test that Config.from_object correctly loads uppercase attributes"""
    config = Config('.')
    
    # Create object with uppercase attributes
    obj = ConfigObject()
    for key, value in config_data.items():
        setattr(obj, key, value)
    
    # Load from object
    config.from_object(obj)
    
    # Property: All uppercase attributes should be loaded
    for key, value in config_data.items():
        assert key in config, f"Config missing key {key}"
        assert config[key] == value, f"Config has wrong value for {key}"


# Test 5: Config from_pyfile with valid Python files
@given(
    config_vars=st.dictionaries(
        st.text(min_size=1, max_size=30).filter(
            lambda x: x.isupper() and x.isidentifier() and not x.startswith('_')
        ),
        st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.text(max_size=50).map(lambda x: repr(x)),  # Properly escape strings
            st.booleans(),
            st.none()
        ),
        min_size=1,
        max_size=10
    )
)
def test_config_from_pyfile(config_vars):
    """Test that Config.from_pyfile correctly loads Python configuration files"""
    config = Config('.')
    
    # Create temporary Python file with config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        for key, value in config_vars.items():
            if isinstance(value, str) and not (value == 'True' or value == 'False' or value == 'None'):
                # Value is already repr'd from the strategy
                f.write(f"{key} = {value}\n")
            else:
                f.write(f"{key} = {value}\n")
        temp_file = f.name
    
    try:
        # Load from Python file
        config.from_pyfile(temp_file)
        
        # Property: All uppercase variables should be loaded
        for key, value in config_vars.items():
            assert key in config, f"Config missing key {key}"
            # Need to eval string values that were repr'd
            expected = eval(value) if isinstance(value, str) and value.startswith("'") else value
            assert config[key] == expected, f"Config has wrong value for {key}: got {config[key]}, expected {expected}"
    finally:
        os.unlink(temp_file)


# Test 6: Response headers handling
@given(
    headers_list=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50).filter(lambda x: ':' not in x and '\n' not in x and '\r' not in x),
            st.text(max_size=100).filter(lambda x: '\n' not in x and '\r' not in x)
        ),
        max_size=20
    ),
    content=st.text(max_size=500)
)
def test_response_headers(headers_list, content):
    """Test that Response correctly handles headers"""
    # Create response with headers
    response = Response(content, headers=headers_list)
    
    # Property: All headers should be set
    for header_name, header_value in headers_list:
        # Headers might be case-insensitive
        assert header_name in response.headers or header_name.lower() in response.headers or header_name.upper() in response.headers
    
    # Property: Content should be preserved
    assert response.get_data(as_text=True) == content