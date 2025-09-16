"""Property-based tests for Flask using Hypothesis"""
import json
import math
from decimal import Decimal

import flask
from flask import Flask, Config
from hypothesis import assume, given, strategies as st
import pytest


# Strategy for JSON-serializable data
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1e10, max_value=1e10),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.text(min_size=0, max_size=100)
)

# Recursive strategy for nested JSON structures
json_data = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            children,
            max_size=10
        )
    ),
    max_leaves=50
)


@given(json_data)
def test_flask_json_round_trip(data):
    """Test that flask.json.dumps/loads is a round-trip operation"""
    # Encode the data
    encoded = flask.json.dumps(data)
    
    # Verify it's a string
    assert isinstance(encoded, str)
    
    # Decode back
    decoded = flask.json.loads(encoded)
    
    # Should be equal
    assert decoded == data


@given(json_data)
def test_flask_json_dumps_consistent_with_stdlib(data):
    """Test that flask.json.dumps produces same output as stdlib json for basic types"""
    flask_output = flask.json.dumps(data, sort_keys=True)
    stdlib_output = json.dumps(data, sort_keys=True)
    
    # Flask and stdlib should produce identical JSON for basic types
    assert flask_output == stdlib_output


@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    json_primitives,
    min_size=0,
    max_size=10
))
def test_flask_config_update_idempotent(config_dict):
    """Test that updating Config twice with same data is idempotent"""
    app = Flask(__name__)
    
    # Get initial state
    initial_keys = set(app.config.keys())
    
    # Update once
    app.config.update(config_dict)
    state_after_first = dict(app.config)
    
    # Update again with same data
    app.config.update(config_dict)
    state_after_second = dict(app.config)
    
    # Should be identical after both updates
    assert state_after_first == state_after_second
    
    # All keys from config_dict should be present
    for key in config_dict:
        assert key in app.config
        assert app.config[key] == config_dict[key]


@given(st.dictionaries(
    st.text(min_size=1, max_size=20).filter(lambda x: x.isupper()),
    json_primitives,
    min_size=1,
    max_size=10
))
def test_flask_config_from_mapping(config_dict):
    """Test Config.from_mapping creates correct config"""
    app = Flask(__name__)
    
    # Use from_mapping
    app.config.from_mapping(config_dict)
    
    # All keys should be present
    for key, value in config_dict.items():
        assert key in app.config
        assert app.config[key] == value


@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    json_primitives,
    min_size=0,
    max_size=10
))
def test_flask_config_get_methods(config_dict):
    """Test Config get methods work correctly"""
    app = Flask(__name__)
    app.config.update(config_dict)
    
    # Test get with existing keys
    for key, value in config_dict.items():
        assert app.config.get(key) == value
        assert app.config.get(key, "default") == value
    
    # Test get with non-existing key
    non_existing = "THIS_KEY_DOES_NOT_EXIST_123456"
    assume(non_existing not in config_dict)
    
    assert app.config.get(non_existing) is None
    assert app.config.get(non_existing, "default") == "default"


# Test for nested structure preservation
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.recursive(
        json_primitives,
        lambda children: st.dictionaries(
            st.text(min_size=1, max_size=10),
            children,
            max_size=5
        ),
        max_leaves=20
    ),
    min_size=1,
    max_size=5
))
def test_flask_json_nested_dict_preservation(nested_dict):
    """Test that deeply nested dictionaries are preserved correctly"""
    encoded = flask.json.dumps(nested_dict)
    decoded = flask.json.loads(encoded)
    
    # Should preserve structure exactly
    assert decoded == nested_dict
    
    # Verify keys are preserved
    assert set(decoded.keys()) == set(nested_dict.keys())


@given(st.lists(json_data, min_size=0, max_size=20))
def test_flask_json_top_level_arrays(array_data):
    """Test that Flask can serialize top-level arrays (added in 0.11)"""
    # Serialize top-level array
    encoded = flask.json.dumps(array_data)
    decoded = flask.json.loads(encoded)
    
    # Should round-trip correctly
    assert decoded == array_data
    assert isinstance(decoded, list)


# Test edge cases for jsonify with app context
@given(json_data)
def test_jsonify_with_app_context(data):
    """Test jsonify within app context"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    with app.app_context():
        # jsonify should create a Response object
        response = flask.jsonify(data)
        
        # Check response properties
        assert response.mimetype == 'application/json'
        assert response.status_code == 200
        
        # The data should be recoverable
        response_data = flask.json.loads(response.get_data(as_text=True))
        assert response_data == data


@given(
    st.lists(json_primitives, min_size=2, max_size=10)
)
def test_jsonify_multiple_args(args):
    """Test jsonify with multiple positional arguments"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    with app.app_context():
        # jsonify with multiple args should create a list
        response = flask.jsonify(*args)
        
        assert response.mimetype == 'application/json'
        
        # Should be serialized as a list
        response_data = flask.json.loads(response.get_data(as_text=True))
        assert response_data == list(args)


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        json_primitives,
        min_size=1,
        max_size=10
    )
)
def test_jsonify_kwargs(kwargs):
    """Test jsonify with keyword arguments"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    with app.app_context():
        # jsonify with kwargs should create a dict
        response = flask.jsonify(**kwargs)
        
        assert response.mimetype == 'application/json'
        
        # Should be serialized as a dict
        response_data = flask.json.loads(response.get_data(as_text=True))
        assert response_data == kwargs