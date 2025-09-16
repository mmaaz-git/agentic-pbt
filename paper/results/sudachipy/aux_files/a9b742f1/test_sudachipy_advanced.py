#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import sudachipy
from sudachipy import config
import json

# Test edge cases in config module

# Test 1: Config with empty strings
@given(
    system=st.sampled_from([None, "", "  "]),
    projection=st.sampled_from([None, "", "  "])
)
def test_config_empty_strings(system, projection):
    try:
        cfg = config.Config(system=system, projection=projection)
        json_str = cfg.as_jsons()
        parsed = json.loads(json_str)
        
        # Empty strings should be preserved if not None
        if system is not None:
            assert "system" in parsed
            assert parsed["system"] == system
        if projection is not None:
            assert "projection" in parsed
            assert parsed["projection"] == projection
    except Exception as e:
        # Check if this is expected behavior
        pass

# Test 2: Config._filter_nulls with nested structures
@given(st.recursive(
    st.one_of(st.none(), st.text(), st.integers()),
    lambda children: st.dictionaries(st.text(min_size=1), children, max_size=3),
    max_leaves=10
))
def test_filter_nulls_nested(data):
    if isinstance(data, dict):
        filtered = config._filter_nulls(data.copy())
        assert None not in filtered.values()
        # Check that only top-level None values are removed
        for k, v in filtered.items():
            assert data[k] == v
            if isinstance(v, dict) and None in v.values():
                # Nested None values should remain
                assert None in v.values()

# Test 3: Config.update with invalid field names
@given(
    field_name=st.text(min_size=1, max_size=50),
    field_value=st.one_of(st.text(), st.integers(), st.none())
)
def test_config_update_invalid_fields(field_name, field_value):
    cfg = config.Config()
    try:
        updated = cfg.update(**{field_name: field_value})
        # If it succeeds, check the field was set
        if hasattr(updated, field_name):
            assert getattr(updated, field_name) == field_value
    except TypeError as e:
        # This is expected for invalid field names
        assert "unexpected keyword argument" in str(e).lower() or "got an unexpected" in str(e).lower()

# Test 4: Config.as_jsons with very large lists
@given(st.lists(st.text(min_size=1, max_size=10), min_size=15, max_size=100))
def test_config_user_list_limit(user_list):
    # Documentation says max 14 user dictionaries
    cfg = config.Config(user=user_list)
    json_str = cfg.as_jsons()
    parsed = json.loads(json_str)
    
    # Should preserve all items even if > 14
    assert "user" in parsed
    assert parsed["user"] == user_list
    assert len(parsed["user"]) == len(user_list)

# Test 5: Config projection field validation
@given(st.text(min_size=1))
def test_config_projection_validation(projection_value):
    valid_projections = ["surface", "normalized", "reading", "dictionary", 
                        "dictionary_and_surface", "normalized_and_surface", "normalized_nouns"]
    
    cfg = config.Config(projection=projection_value)
    json_str = cfg.as_jsons()
    parsed = json.loads(json_str)
    
    # Any string value should be accepted (no validation in Config class)
    assert "projection" in parsed
    assert parsed["projection"] == projection_value

# Test 6: Config with special characters in JSON
@given(
    system=st.text().filter(lambda x: any(c in x for c in ['"', '\\', '\n', '\r', '\t'])),
)
def test_config_json_special_chars(system):
    assume(system)  # Skip empty strings
    cfg = config.Config(system=system)
    json_str = cfg.as_jsons()
    
    # Should properly escape special characters
    parsed = json.loads(json_str)
    assert parsed.get("system") == system
    
    # Round-trip should preserve the value
    re_serialized = json.dumps(parsed)
    re_parsed = json.loads(re_serialized)
    assert re_parsed.get("system") == system

# Test 7: _filter_nulls mutation check
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.none(), st.text(), st.integers()),
    min_size=1, max_size=5
))
def test_filter_nulls_mutates_input(data):
    original = data.copy()
    filtered = config._filter_nulls(data)
    
    # Check if input was mutated
    if None in original.values():
        # The function mutates the input dict!
        assert data != original
        assert filtered is data  # Returns the same object
    else:
        assert data == original  # No change if no None values

# Test 8: Config fields are None by default
def test_config_default_values():
    cfg = config.Config()
    
    # All fields except projection should be None by default
    assert cfg.system is None
    assert cfg.user is None
    assert cfg.projection == "surface"  # Has a default
    assert cfg.connectionCostPlugin is None
    assert cfg.oovProviderPlugin is None
    assert cfg.pathRewritePlugin is None
    assert cfg.inputTextPlugin is None
    assert cfg.characterDefinitionFile is None