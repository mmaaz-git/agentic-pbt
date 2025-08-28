#!/usr/bin/env python3
import json
import string
from hypothesis import given, strategies as st, assume, settings
import flask
from flask import Config
import tempfile
import os


# Test 1: JSON round-trip property
@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
            st.text(min_size=0, max_size=1000)
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=50),
            st.dictionaries(st.text(min_size=1, max_size=100), children, max_size=50)
        ),
        max_leaves=100
    )
)
@settings(max_examples=1000)
def test_json_round_trip(data):
    """Test that flask.json.dumps/loads preserves data correctly"""
    encoded = flask.json.dumps(data)
    decoded = flask.json.loads(encoded)
    assert data == decoded


# Test 2: Config.from_mapping only adds uppercase keys
@given(
    st.dictionaries(
        st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=50),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.text(),
            st.lists(st.integers()),
            st.dictionaries(st.text(), st.integers())
        ),
        min_size=0,
        max_size=20
    )
)
def test_config_from_mapping_uppercase_only(mapping):
    """Test that Config.from_mapping only adds uppercase keys"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(tmpdir)
        original_keys = set(config.keys())
        
        result = config.from_mapping(mapping)
        assert result is True
        
        # Check that only uppercase keys were added
        new_keys = set(config.keys()) - original_keys
        for key in new_keys:
            assert key.isupper()
            assert key in mapping
            assert config[key] == mapping[key]
        
        # Check that lowercase keys were not added
        for key in mapping:
            if not key.isupper() and key not in original_keys:
                assert key not in config


# Test 3: Config.get_namespace invariants
@given(
    # Generate config dict with prefixed keys
    st.dictionaries(
        st.text(alphabet=string.ascii_uppercase + "_", min_size=1, max_size=20),
        st.one_of(st.none(), st.booleans(), st.integers(), st.text()),
        min_size=0,
        max_size=10
    ),
    # Generate namespace to query
    st.text(alphabet=string.ascii_uppercase + "_", min_size=1, max_size=10),
    st.booleans(),  # lowercase
    st.booleans()   # trim_namespace
)
def test_config_get_namespace_properties(config_dict, namespace, lowercase, trim_namespace):
    """Test Config.get_namespace properties"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(tmpdir)
        config.update(config_dict)
        
        result = config.get_namespace(namespace, lowercase=lowercase, trim_namespace=trim_namespace)
        
        # All keys in result should start with namespace in original config
        for result_key in result:
            if trim_namespace:
                if lowercase:
                    original_key = namespace + result_key.upper()
                else:
                    original_key = namespace + result_key
            else:
                if lowercase:
                    original_key = result_key.upper()
                else:
                    original_key = result_key
            
            assert original_key in config
            assert config[original_key] == result[result_key]
        
        # All config keys starting with namespace should be in result
        for config_key in config:
            if config_key.startswith(namespace):
                if trim_namespace:
                    result_key = config_key[len(namespace):]
                else:
                    result_key = config_key
                
                if lowercase:
                    result_key = result_key.lower()
                
                assert result_key in result
                assert result[result_key] == config[config_key]


# Test 4: Config round-trip through from_object
@given(
    st.dictionaries(
        st.text(alphabet=string.ascii_uppercase + "_", min_size=1, max_size=20),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.text(max_size=1000),
            st.lists(st.integers(), max_size=10)
        ),
        min_size=0,
        max_size=10
    )
)
def test_config_from_object_preserves_uppercase(config_dict):
    """Test that Config.from_object preserves uppercase attributes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a class with the config values
        class TestConfig:
            pass
        
        for key, value in config_dict.items():
            setattr(TestConfig, key, value)
        
        # Also add some lowercase attributes that should be ignored
        TestConfig.lowercase_key = "should_be_ignored"
        TestConfig._private = "should_be_ignored"
        
        config = Config(tmpdir)
        config.from_object(TestConfig)
        
        # Check all uppercase keys were copied
        for key, value in config_dict.items():
            assert key in config
            assert config[key] == value
        
        # Check lowercase keys were not copied
        assert "lowercase_key" not in config
        assert "_private" not in config


# Test 5: JSON serialization with special types
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
            st.text(max_size=100)
        ),
        min_size=0,
        max_size=10
    )
)
def test_json_dumps_loads_dict_ordering(data):
    """Test that dict key ordering is preserved through dumps/loads"""
    # Python 3.7+ guarantees dict ordering
    encoded = flask.json.dumps(data)
    decoded = flask.json.loads(encoded)
    
    # The decoded dict should equal the original
    assert decoded == data
    
    # If we have a dict, check if keys are in the same order after sorting
    # (Flask's DefaultJSONProvider has sort_keys=True by default)
    if isinstance(data, dict) and data:
        # Keys should be sorted in the JSON output
        import json
        standard_encoded = json.dumps(data, sort_keys=True)
        standard_decoded = json.loads(standard_encoded)
        assert list(decoded.keys()) == list(standard_decoded.keys())


# Test 6: Empty input edge cases
def test_json_empty_edge_cases():
    """Test JSON handling of empty inputs"""
    # Empty string should fail
    try:
        flask.json.loads("")
        assert False, "Should have raised an error for empty string"
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Empty dict/list should work
    assert flask.json.loads("{}") == {}
    assert flask.json.loads("[]") == []
    
    # Whitespace-only should fail
    try:
        flask.json.loads("   ")
        assert False, "Should have raised an error for whitespace-only string"
    except (json.JSONDecodeError, ValueError):
        pass


# Test 7: Config.from_mapping with kwargs
@given(
    st.dictionaries(
        st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=20),
        st.one_of(st.none(), st.booleans(), st.integers(), st.text()),
        min_size=0,
        max_size=5
    ),
    st.dictionaries(
        st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=20),
        st.one_of(st.none(), st.booleans(), st.integers(), st.text()),
        min_size=0,
        max_size=5
    )
)
def test_config_from_mapping_with_kwargs(mapping, kwargs):
    """Test Config.from_mapping with both mapping and kwargs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Config(tmpdir)
        
        # from_mapping should handle both mapping and kwargs
        result = config.from_mapping(mapping, **kwargs)
        assert result is True
        
        # kwargs should override mapping for same keys
        combined = dict(mapping)
        combined.update(kwargs)
        
        for key, value in combined.items():
            if key.isupper():
                assert key in config
                assert config[key] == value
            else:
                assert key not in config


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])