"""Additional property-based tests for Flask edge cases"""
import flask
from flask import Flask, Response
from hypothesis import assume, given, strategies as st
import pytest


# Test for special characters in JSON keys
@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    st.integers(),
    min_size=1,
    max_size=10
))
def test_flask_json_special_key_characters(data):
    """Test JSON handling with special characters in keys"""
    # Skip if any key contains null bytes (not valid in JSON)
    assume(all('\x00' not in key for key in data.keys()))
    
    encoded = flask.json.dumps(data)
    decoded = flask.json.loads(encoded)
    
    # Keys should be preserved exactly
    assert decoded == data
    assert set(decoded.keys()) == set(data.keys())


# Test make_response with various input types
@given(st.one_of(
    st.text(max_size=1000),
    st.binary(max_size=1000),
    st.dictionaries(st.text(min_size=1, max_size=20), st.integers(), max_size=10),
    st.lists(st.integers(), max_size=20),
    st.tuples(st.text(max_size=100)),
    st.tuples(st.text(max_size=100), st.integers(200, 599)),
    st.tuples(st.text(max_size=100), st.integers(200, 599), st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100), max_size=5))
))
def test_make_response_various_inputs(response_data):
    """Test make_response with various input types"""
    app = Flask(__name__)
    
    with app.app_context():
        try:
            response = flask.make_response(response_data)
            
            # Should always return a Response object
            assert isinstance(response, Response)
            
            # Status code should be valid HTTP status
            assert 100 <= response.status_code < 600
            
            # If input was a tuple with status, it should be preserved
            if isinstance(response_data, tuple) and len(response_data) >= 2:
                if isinstance(response_data[1], int):
                    assert response.status_code == response_data[1]
                    
        except (TypeError, ValueError):
            # Some inputs might not be valid for make_response
            # This is expected for certain input types
            pass


# Test Config with special key names
@given(st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=100)),
    min_size=1,
    max_size=20
))
def test_config_special_keys(config_data):
    """Test Config with various key names including reserved Python keywords"""
    app = Flask(__name__)
    
    # Update config
    app.config.update(config_data)
    
    # All keys should be accessible
    for key, value in config_data.items():
        assert key in app.config
        assert app.config[key] == value
        assert app.config.get(key) == value


# Test JSON with Unicode edge cases
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=0, max_size=100),
    min_size=1,
    max_size=10
))
def test_flask_json_unicode_preservation(data):
    """Test that Flask preserves Unicode characters correctly in JSON"""
    # Skip if any string contains null bytes
    assume(all('\x00' not in str(v) for v in data.values()))
    assume(all('\x00' not in k for k in data.keys()))
    
    encoded = flask.json.dumps(data, ensure_ascii=False)
    decoded = flask.json.loads(encoded)
    
    # Unicode should be preserved
    assert decoded == data
    
    # Check each string is preserved exactly
    for key, value in data.items():
        assert decoded[key] == value


# Test empty containers
@given(st.one_of(
    st.just([]),
    st.just({}),
    st.just(""),
    st.just(None)
))
def test_flask_json_empty_containers(empty_data):
    """Test JSON handling of empty containers and None"""
    encoded = flask.json.dumps(empty_data)
    decoded = flask.json.loads(encoded)
    
    assert decoded == empty_data
    
    # Verify type is preserved
    assert type(decoded) == type(empty_data)


# Test jsonify with no arguments
def test_jsonify_no_args():
    """Test jsonify with no arguments (should serialize None)"""
    app = Flask(__name__)
    
    with app.app_context():
        response = flask.jsonify()
        
        assert response.mimetype == 'application/json'
        assert response.status_code == 200
        
        # Should serialize as null
        data = flask.json.loads(response.get_data(as_text=True))
        assert data is None


# Test large JSON structures
@given(st.lists(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=1,
        max_size=10
    ),
    min_size=100,
    max_size=200
))
def test_flask_json_large_structures(large_list):
    """Test JSON handling with large data structures"""
    encoded = flask.json.dumps(large_list)
    decoded = flask.json.loads(encoded)
    
    # Should handle large structures correctly
    assert decoded == large_list
    assert len(decoded) == len(large_list)