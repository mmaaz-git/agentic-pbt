"""Property-based tests for Flask using Hypothesis"""

import json
import string
from hypothesis import given, strategies as st, assume, settings
import flask
import flask.json as fjson
from flask import Flask, Config, jsonify
import pytest
import math


# Test 1: Flask JSON round-trip property
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_flask_json_round_trip(data):
    """Test that Flask JSON encoding/decoding is reversible"""
    app = Flask(__name__)
    with app.app_context():
        json_str = fjson.dumps(data)
        decoded = fjson.loads(json_str)
        assert decoded == data


# Test 2: Flask Config update preserves existing values
@given(
    initial=st.dictionaries(
        st.text(min_size=1).filter(lambda x: x.isupper()),
        st.one_of(st.integers(), st.text(), st.booleans())
    ),
    update=st.dictionaries(
        st.text(min_size=1).filter(lambda x: x.isupper()),
        st.one_of(st.integers(), st.text(), st.booleans())
    )
)
def test_config_update_preserves_values(initial, update):
    """Test that Config.update preserves non-overlapping keys"""
    config = Config('.')
    config.update(initial)
    
    # Store original values for non-overlapping keys
    preserved_keys = set(initial.keys()) - set(update.keys())
    preserved_values = {k: config[k] for k in preserved_keys}
    
    config.update(update)
    
    # Check preserved keys still have original values
    for key in preserved_keys:
        assert config[key] == preserved_values[key]
    
    # Check updated keys have new values
    for key, value in update.items():
        assert config[key] == value


# Test 3: Config.get_namespace returns consistent prefixed values
@given(
    config_dict=st.dictionaries(
        st.text(min_size=1, alphabet=string.ascii_uppercase + '_', max_size=20),
        st.one_of(st.integers(), st.text(), st.booleans()),
        min_size=1
    ),
    namespace=st.text(min_size=1, alphabet=string.ascii_uppercase, max_size=10)
)
def test_config_namespace_consistency(config_dict, namespace):
    """Test that get_namespace returns only prefixed values"""
    config = Config('.')
    
    # Add values with and without prefix
    prefixed_dict = {f"{namespace}_{k}": v for k, v in config_dict.items()}
    other_dict = {f"OTHER_{k}": v for k, v in config_dict.items()}
    
    config.update(prefixed_dict)
    config.update(other_dict)
    
    # Get namespace
    ns = config.get_namespace(namespace + '_')
    
    # Check all returned values are from prefixed keys
    for key, value in ns.items():
        original_key = f"{namespace}_{key}"
        assert original_key in config
        assert config[original_key] == value
    
    # Check no OTHER_ values are included
    assert len(ns) == len(config_dict)


# Test 4: Flask jsonify creates valid Response objects
@given(
    data=st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text())
    )
)
def test_jsonify_creates_valid_response(data):
    """Test that jsonify creates Response with correct content type"""
    app = Flask(__name__)
    with app.app_context():
        response = jsonify(data)
        
        # Check it's a Response object
        assert isinstance(response, flask.Response)
        
        # Check content type
        assert response.content_type.startswith('application/json')
        
        # Check data round-trips correctly
        decoded = json.loads(response.get_data(as_text=True))
        assert decoded == data


# Test 5: Config from_mapping preserves all mappings
@given(
    mappings=st.lists(
        st.dictionaries(
            st.text(min_size=1).filter(lambda x: x.isupper()),
            st.one_of(st.integers(), st.text(), st.booleans()),
            min_size=1
        ),
        min_size=1,
        max_size=5
    )
)
def test_config_from_mapping_preserves_all(mappings):
    """Test that from_mapping with multiple dicts preserves later values"""
    config = Config('.')
    config.from_mapping(*mappings)
    
    # Build expected result (later mappings override earlier ones)
    expected = {}
    for mapping in mappings:
        expected.update(mapping)
    
    # Check all expected values are present
    for key, value in expected.items():
        assert config[key] == value


# Test 6: Flask JSON handles special float values differently than standard JSON
@given(st.floats())
def test_flask_json_float_handling(value):
    """Test Flask JSON handling of special float values"""
    app = Flask(__name__)
    with app.app_context():
        if math.isnan(value) or math.isinf(value):
            # Flask JSON should handle NaN and Infinity
            result = fjson.dumps(value)
            assert result in ['NaN', 'Infinity', '-Infinity', 'null']
        else:
            # Normal floats should round-trip
            json_str = fjson.dumps(value)
            decoded = fjson.loads(json_str)
            if value != 0.0:  # Avoid -0.0 vs 0.0 issues
                assert math.isclose(decoded, value, rel_tol=1e-15)


# Test 7: Config keys must be strings and uppercase for some methods
@given(
    key=st.text(min_size=1),
    value=st.one_of(st.integers(), st.text(), st.booleans())
)
def test_config_uppercase_enforcement(key, value):
    """Test that Config enforces uppercase for environment-like access"""
    config = Config('.')
    
    # Setting with non-uppercase should work
    config[key] = value
    assert config[key] == value
    
    # If key has lowercase, uppercase version should not exist unless explicitly set
    if key != key.upper():
        assert key.upper() not in config or config[key.upper()] != value


# Test 8: Testing Flask request context pushing/popping invariant
def test_flask_context_stack_invariant():
    """Test that app context push/pop maintains stack invariant"""
    app = Flask(__name__)
    
    # Initially no context
    assert not flask.has_app_context()
    
    # Push context
    ctx = app.app_context()
    ctx.push()
    assert flask.has_app_context()
    
    # Pop context
    ctx.pop()
    assert not flask.has_app_context()


# Test 9: Config.from_object with module names
@given(
    settings=st.dictionaries(
        st.from_regex(r'^[A-Z][A-Z_]*$', fullmatch=True).filter(lambda x: len(x) <= 20),
        st.one_of(st.integers(), st.text(max_size=100), st.booleans()),
        min_size=1,
        max_size=10
    )
)
def test_config_from_object_module(settings):
    """Test Config.from_object with a mock module object"""
    config = Config('.')
    
    # Create a mock module object
    class MockModule:
        pass
    
    module = MockModule()
    for key, value in settings.items():
        setattr(module, key, value)
    
    # Load from object
    config.from_object(module)
    
    # Verify all uppercase attributes were loaded
    for key, value in settings.items():
        if key.isupper():
            assert config[key] == value


# Test 10: Flask JSON preserves dict key order
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.integers(),
        min_size=2,
        max_size=10
    )
)
def test_flask_json_preserves_dict_order(data):
    """Test that Flask JSON preserves dictionary key order"""
    app = Flask(__name__)
    with app.app_context():
        json_str = fjson.dumps(data)
        decoded = fjson.loads(json_str)
        
        # In Python 3.7+, dicts maintain insertion order
        assert list(decoded.keys()) == list(data.keys())
        assert decoded == data