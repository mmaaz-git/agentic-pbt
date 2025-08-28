"""Extended property-based tests for Flask to find more bugs"""

import tempfile
import os
import sys
from hypothesis import given, strategies as st, assume, settings
import flask
from flask import json, Response, Config, Request
from flask.testing import FlaskClient
from werkzeug.test import Client
from werkzeug.serving import WSGIRequestHandler
import json as std_json


# Test 7: Config update operations preserve dict properties
@given(
    initial_data=st.dictionaries(
        st.text(min_size=1, max_size=30).filter(lambda x: x.isupper() and x.isidentifier()),
        st.one_of(st.integers(), st.text(max_size=50), st.booleans()),
        min_size=1,
        max_size=10
    ),
    update_data=st.dictionaries(
        st.text(min_size=1, max_size=30).filter(lambda x: x.isupper() and x.isidentifier()),
        st.one_of(st.integers(), st.text(max_size=50), st.booleans()),
        max_size=10
    )
)
def test_config_update_operations(initial_data, update_data):
    """Test that Config update operations work correctly"""
    config = Config('.')
    
    # Initialize config
    config.from_mapping(initial_data)
    initial_len = len(config)
    
    # Update config
    config.update(update_data)
    
    # Property: All update keys should be present
    for key in update_data:
        assert key in config
        assert config[key] == update_data[key]
    
    # Property: Original keys not in update should remain
    for key in initial_data:
        if key not in update_data:
            assert config[key] == initial_data[key]


# Test 8: JSON encoding with special Unicode characters
@given(
    unicode_strings=st.lists(
        st.text(min_size=1).filter(lambda x: any(ord(c) > 127 for c in x)),
        min_size=1,
        max_size=10
    )
)
def test_json_unicode_handling(unicode_strings):
    """Test that Flask JSON handles Unicode correctly"""
    data = {"strings": unicode_strings}
    
    # Encode and decode
    encoded = json.dumps(data)
    decoded = json.loads(encoded)
    
    # Property: Unicode should be preserved
    assert decoded == data
    
    # Property: Should be valid UTF-8
    encoded.encode('utf-8')


# Test 9: Config get with defaults
@given(
    config_data=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda x: x.isupper() and x.isidentifier()),
        st.one_of(st.integers(), st.text(max_size=50)),
        max_size=10
    ),
    default_value=st.one_of(st.integers(), st.text(max_size=50), st.none())
)
@settings(suppress_health_check=[])
def test_config_get_with_defaults(config_data, default_value):
    """Test Config.get with default values"""
    # Generate a key that's definitely not in config_data
    missing_key = "DEFINITELY_MISSING_KEY_XYZ"
    
    config = Config('.')
    config.from_mapping(config_data)
    
    # Property: get should return default for missing keys
    assert config.get(missing_key, default_value) == default_value
    
    # Property: get should return actual value for existing keys
    for key, value in config_data.items():
        assert config.get(key, "DEFAULT") == value


# Test 10: Response mimetype handling
@given(
    content=st.text(max_size=500),
    mimetype=st.sampled_from(['text/plain', 'text/html', 'application/json', 'application/xml'])
)
def test_response_mimetype(content, mimetype):
    """Test that Response correctly handles MIME types"""
    response = Response(content, mimetype=mimetype)
    
    # Property: MIME type should be preserved
    assert response.mimetype == mimetype
    
    # Property: Content-Type header should include MIME type
    assert mimetype in response.content_type


# Test 11: Config from JSON file
@given(
    json_data=st.dictionaries(
        st.text(min_size=1, max_size=30).filter(lambda x: x.isupper() and x.isidentifier()),
        st.one_of(
            st.integers(min_value=-1000, max_value=1000),
            st.text(max_size=50),
            st.booleans(),
            st.none(),
            st.lists(st.integers(), max_size=5)
        ),
        min_size=1,
        max_size=10
    )
)
def test_config_from_json(json_data):
    """Test Config.from_json method if available"""
    config = Config('.')
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        std_json.dump(json_data, f)
        temp_file = f.name
    
    try:
        # from_file requires a load function
        config.from_file(temp_file, load=std_json.load)
        
        # Property: All JSON keys should be loaded
        for key, value in json_data.items():
            if key in config:  # Only check if it was loaded
                assert config[key] == value
    except (AttributeError, TypeError) as e:
        # from_file might not exist or have different signature
        pass
    finally:
        os.unlink(temp_file)


# Test 12: Response data consistency
@given(
    data=st.one_of(
        st.binary(max_size=1000),
        st.text(max_size=1000).map(lambda x: x.encode('utf-8'))
    ),
    status=st.integers(min_value=200, max_value=599)
)
def test_response_data_consistency(data, status):
    """Test that Response maintains data consistency"""
    response = Response(data, status=status)
    
    # Property: get_data should return the same data
    assert response.get_data() == data
    
    # Property: Status should be preserved
    assert response.status_code == status
    
    # Property: data attribute should match
    assert response.data == data


# Test 13: Config pop operation
@given(
    config_data=st.dictionaries(
        st.sampled_from(['DEBUG', 'TESTING', 'SECRET_KEY', 'DATABASE_URL', 'API_KEY', 'PORT', 'HOST']),
        st.one_of(st.integers(), st.text(max_size=50)),
        min_size=2,  # Need at least 2 items
        max_size=7
    )
)
def test_config_pop(config_data):
    """Test Config.pop operation"""
    config = Config('.')
    config.from_mapping(config_data)
    
    # Pick a key to pop
    key_to_pop = list(config_data.keys())[0]
    expected_value = config_data[key_to_pop]
    initial_len = len(config)
    
    # Pop the key
    popped_value = config.pop(key_to_pop)
    
    # Property: Should return the correct value
    assert popped_value == expected_value
    
    # Property: Key should be removed
    assert key_to_pop not in config
    
    # Property: Length should decrease by 1
    assert len(config) == initial_len - 1
    
    # Property: Other keys should remain
    for key in config_data:
        if key != key_to_pop:
            assert config[key] == config_data[key]


# Test 14: JSON with circular references protection
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.integers(), st.text(max_size=50)),
        min_size=1,
        max_size=5
    )
)
def test_json_no_circular_refs(data):
    """Test that Flask JSON handles nested structures without circular refs"""
    # Create nested structure
    nested = {"data": data, "meta": {"count": len(data)}}
    
    # Should encode without issues
    encoded = json.dumps(nested)
    decoded = json.loads(encoded)
    
    # Property: Structure should be preserved
    assert decoded == nested