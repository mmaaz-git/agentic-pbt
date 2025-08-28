#!/usr/bin/env python3
"""Additional property-based tests for sudachipy"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import sudachipy
from sudachipy import SplitMode
from sudachipy.config import Config


# Test SplitMode None behavior - should default to C
def test_splitmode_none_default():
    """Test that None defaults to SplitMode.C as documented"""
    mode_none = SplitMode(None)
    mode_c = SplitMode("C")
    
    # They should be equal if None defaults to C
    assert mode_none == mode_c, f"SplitMode(None) = {mode_none}, should equal SplitMode.C = {mode_c}"


# Test Config defaults
def test_config_defaults():
    """Test that Config has correct default values"""
    config = Config()
    
    # Check documented defaults
    assert config.projection == "surface", f"Default projection should be 'surface', got {config.projection}"
    
    # Check that None fields are actually None
    assert config.system is None
    assert config.user is None
    assert config.connectionCostPlugin is None
    assert config.oovProviderPlugin is None
    assert config.pathRewritePlugin is None
    assert config.inputTextPlugin is None
    assert config.characterDefinitionFile is None


# Test empty string mode behavior
def test_splitmode_empty_string():
    """Test how SplitMode handles empty string"""
    try:
        mode = SplitMode("")
        print(f"Unexpected: SplitMode('') succeeded with {mode}")
        assert False, "Empty string should not be a valid mode"
    except sudachipy.errors.SudachiError as e:
        # Expected
        assert "Mode must be" in str(e)


# Test Config projection field validation
@given(st.text())
def test_config_projection_accepts_any_string(projection):
    """Test if Config.projection accepts any string or only specific values"""
    # Based on documentation, valid values are:
    # surface, normalized, reading, dictionary, dictionary_and_surface, 
    # normalized_and_surface, normalized_nouns
    
    config = Config(projection=projection)
    assert config.projection == projection
    
    # Should serialize without error
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    
    # The projection should be in the JSON
    if projection != "surface":  # surface is the default
        assert parsed.get("projection") == projection


# Test if Config correctly filters multiple None values
@given(
    st.fixed_dictionaries({
        'system': st.one_of(st.none(), st.text()),
        'user': st.one_of(st.none(), st.lists(st.text(), max_size=3)),
        'projection': st.one_of(st.none(), st.text()),
        'connectionCostPlugin': st.one_of(st.none(), st.lists(st.text())),
        'oovProviderPlugin': st.one_of(st.none(), st.lists(st.text())),
        'pathRewritePlugin': st.one_of(st.none(), st.lists(st.text())),
        'inputTextPlugin': st.one_of(st.none(), st.lists(st.text())),
        'characterDefinitionFile': st.one_of(st.none(), st.text()),
    })
)
def test_config_none_filtering_comprehensive(kwargs):
    """Test that all None values are properly filtered in JSON output"""
    config = Config(**kwargs)
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    
    # Check that no None values exist in the output
    for key, value in parsed.items():
        assert value is not None, f"Key {key} has None value in JSON output"
    
    # Check that non-None values are preserved
    for key, value in kwargs.items():
        if value is not None:
            if key == "projection" and value == "surface":
                # surface is the default, might not be in output
                continue
            assert key in parsed, f"Non-None key {key} missing from JSON output"
            assert parsed[key] == value, f"Value mismatch for {key}: expected {value}, got {parsed[key]}"


# Test edge case: Can Config handle very large user dictionary lists?
@given(st.lists(st.text(min_size=1), min_size=15, max_size=20))
def test_config_too_many_user_dicts(user_dicts):
    """Test if Config enforces the 14 user dictionary limit mentioned in documentation"""
    # Documentation says "maximum number of user dictionaries is 14"
    config = Config(user=user_dicts)
    
    # It accepts the value without validation
    assert config.user == user_dicts
    
    # Can still serialize to JSON
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    assert parsed.get("user") == user_dicts


if __name__ == "__main__":
    print("Running additional property-based tests...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])