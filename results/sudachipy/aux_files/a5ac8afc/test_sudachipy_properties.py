#!/usr/bin/env python3
"""Property-based tests for sudachipy.dictionary module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import sudachipy
from sudachipy import SplitMode
from sudachipy.config import Config
from sudachipy import errors
import sudachipy.__init__ as sudachipy_init


# Test 1: SplitMode string parsing property
# The documentation says SplitMode accepts ["A", "a", "B", "b", "C", "c", None]
@given(st.sampled_from(["A", "a", "B", "b", "C", "c", None]))
def test_splitmode_valid_strings(mode_str):
    """Valid mode strings should create SplitMode objects without errors"""
    mode = SplitMode(mode_str)
    assert mode is not None
    assert isinstance(mode, SplitMode)


@given(st.text())
def test_splitmode_case_insensitivity(text):
    """Test if SplitMode properly handles case for valid mode letters"""
    # According to the documentation, only A, B, C are valid
    if text.upper() in ["A", "B", "C"]:
        mode_upper = SplitMode(text.upper())
        mode_lower = SplitMode(text.lower())
        # Both should succeed
        assert mode_upper is not None
        assert mode_lower is not None


@given(st.text().filter(lambda x: x.upper() not in ["A", "B", "C", ""]))
def test_splitmode_invalid_strings(text):
    """Test that invalid strings either raise error or default to C"""
    # Based on documentation, invalid strings should default to C (when None is passed)
    # Let's test what actually happens
    try:
        mode = SplitMode(text)
        # If it doesn't raise an error, it should return some mode
        assert mode is not None
        assert isinstance(mode, SplitMode)
    except (ValueError, TypeError) as e:
        # If it raises an error, that's also acceptable behavior
        pass


# Test 2: Config JSON serialization property
@given(
    system=st.one_of(st.none(), st.text()),
    projection=st.one_of(st.none(), st.sampled_from(["surface", "normalized", "reading", "dictionary"])),
    characterDefinitionFile=st.one_of(st.none(), st.text())
)
def test_config_json_serialization(system, projection, characterDefinitionFile):
    """Config.as_jsons() should produce valid JSON with None values filtered"""
    config = Config(
        system=system,
        projection=projection,
        characterDefinitionFile=characterDefinitionFile
    )
    
    json_str = config.as_jsons()
    
    # Should produce valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # None values should be filtered out
    for key, value in parsed.items():
        assert value is not None
    
    # Non-None values should be preserved
    if system is not None:
        assert parsed.get("system") == system
    else:
        assert "system" not in parsed
        
    if projection is not None:
        assert parsed.get("projection") == projection
    # Note: projection has a default value of "surface"
    
    if characterDefinitionFile is not None:
        assert parsed.get("characterDefinitionFile") == characterDefinitionFile
    else:
        assert "characterDefinitionFile" not in parsed


# Test 3: Config update property
@given(
    initial_system=st.one_of(st.none(), st.text()),
    new_system=st.text(),
    initial_projection=st.one_of(st.none(), st.text()),
    new_projection=st.text()
)
def test_config_update(initial_system, new_system, initial_projection, new_projection):
    """Config.update() should return a new Config with updated fields"""
    config = Config(system=initial_system, projection=initial_projection)
    
    # Update with new values
    updated = config.update(system=new_system, projection=new_projection)
    
    # Original should be unchanged
    assert config.system == initial_system
    if initial_projection is not None:
        assert config.projection == initial_projection
    
    # Updated should have new values
    assert updated.system == new_system
    assert updated.projection == new_projection
    
    # Should be different objects
    assert config is not updated


# Test 4: Config with user dictionaries
@given(st.lists(st.text(), max_size=14))
def test_config_user_dictionaries(user_dicts):
    """Config should accept up to 14 user dictionaries"""
    config = Config(user=user_dicts)
    assert config.user == user_dicts
    
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    
    if user_dicts:
        assert parsed.get("user") == user_dicts
    else:
        # Empty list might be filtered or preserved
        assert parsed.get("user", []) == user_dicts


# Test 5: _find_dict_path validation
@given(st.text())
def test_find_dict_path_validation(dict_type):
    """_find_dict_path should only accept 'small', 'core', or 'full'"""
    if dict_type not in ['small', 'core', 'full']:
        try:
            result = sudachipy_init._find_dict_path(dict_type)
            # Should raise ValueError for invalid dict_type
            assert False, f"Expected ValueError for dict_type={dict_type}"
        except ValueError as e:
            assert "must be" in str(e)
            assert "small" in str(e) and "core" in str(e) and "full" in str(e)
        except ModuleNotFoundError:
            # This is expected when the dictionary is not installed
            pass
    else:
        try:
            result = sudachipy_init._find_dict_path(dict_type)
            # If successful, should return a path
            assert isinstance(result, str)
        except ModuleNotFoundError as e:
            # Expected when dictionary package is not installed
            assert f'sudachidict_{dict_type}' in str(e)
            assert 'pip install' in str(e)


# Test 6: Config field types
@given(
    st.builds(
        Config,
        system=st.one_of(st.none(), st.text()),
        user=st.one_of(st.none(), st.lists(st.text(), max_size=14)),
        projection=st.one_of(st.none(), st.text()),
        connectionCostPlugin=st.one_of(st.none(), st.lists(st.text())),
        oovProviderPlugin=st.one_of(st.none(), st.lists(st.text())),
        pathRewritePlugin=st.one_of(st.none(), st.lists(st.text())),
        inputTextPlugin=st.one_of(st.none(), st.lists(st.text())),
        characterDefinitionFile=st.one_of(st.none(), st.text())
    )
)
def test_config_construction(config):
    """Config should be constructible with various field combinations"""
    assert isinstance(config, Config)
    
    # Test JSON serialization doesn't crash
    json_str = config.as_jsons()
    assert isinstance(json_str, str)
    
    # Test it produces valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)


# Test 7: Test that SplitMode constants exist and are distinct
def test_splitmode_constants():
    """SplitMode.A, B, C should exist and be distinct"""
    modes = [SplitMode.A, SplitMode.B, SplitMode.C]
    
    # All should exist
    for mode in modes:
        assert mode is not None
        assert isinstance(mode, SplitMode)
    
    # Should be distinct
    assert SplitMode.A != SplitMode.B
    assert SplitMode.B != SplitMode.C
    assert SplitMode.A != SplitMode.C


# Test 8: Config JSON round-trip property
@given(
    st.builds(
        Config,
        system=st.one_of(st.none(), st.text(min_size=1)),
        user=st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=5)),
        projection=st.one_of(st.none(), st.sampled_from(["surface", "normalized", "reading"])),
    )
)
def test_config_json_roundtrip(config):
    """Config values should survive JSON serialization/deserialization"""
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    
    # Check that non-None values are preserved
    if config.system is not None:
        assert parsed.get("system") == config.system
    if config.user is not None:
        assert parsed.get("user") == config.user
    if config.projection is not None and config.projection != "surface":  # "surface" is default
        assert parsed.get("projection") == config.projection


if __name__ == "__main__":
    print("Running property-based tests for sudachipy.dictionary...")
    import pytest
    pytest.main([__file__, "-v"])