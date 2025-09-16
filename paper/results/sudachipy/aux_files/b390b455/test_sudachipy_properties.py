#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import sudachipy
from sudachipy import SplitMode, Config, errors

# Property 1: SplitMode case insensitivity
@given(st.sampled_from(['A', 'a', 'B', 'b', 'C', 'c']))
def test_splitmode_case_insensitive(mode_str):
    """Test that SplitMode is case-insensitive as documented."""
    upper_mode = mode_str.upper()
    lower_mode = mode_str.lower()
    
    mode_from_upper = SplitMode(upper_mode)
    mode_from_lower = SplitMode(lower_mode)
    
    # Both should produce the same result
    assert mode_from_upper == mode_from_lower
    
    # And should match the corresponding class attribute
    expected = getattr(SplitMode, upper_mode)
    assert mode_from_upper == expected
    assert mode_from_lower == expected

# Property 2: SplitMode None defaults to C
@given(st.none())
def test_splitmode_none_defaults_to_c(none_value):
    """Test that None defaults to SplitMode.C as documented."""
    result = SplitMode(none_value)
    assert result == SplitMode.C

# Property 3: SplitMode invalid strings raise error
@given(st.text().filter(lambda s: s.upper() not in ['A', 'B', 'C']))
def test_splitmode_invalid_raises_error(invalid_str):
    """Test that invalid mode strings raise SudachiError."""
    assume(invalid_str is not None)  # None has special behavior
    
    try:
        SplitMode(invalid_str)
        assert False, f"Expected SudachiError for {repr(invalid_str)}"
    except errors.SudachiError as e:
        # Expected behavior
        assert "Mode must be one of" in str(e)

# Property 4: Config update creates new object (immutability)
@given(
    st.one_of(st.none(), st.text()),  # system
    st.one_of(st.none(), st.lists(st.text(), max_size=14)),  # user
    st.sampled_from(["surface", "normalized", "reading", "dictionary", 
                     "dictionary_and_surface", "normalized_and_surface", "normalized_nouns"]),  # projection
)
def test_config_update_immutability(system, user, projection):
    """Test that Config.update() returns a new object without modifying the original."""
    original = Config()
    original_system = original.system
    original_user = original.user
    original_projection = original.projection
    
    # Update with new values
    updated = original.update(system=system, user=user, projection=projection)
    
    # Original should be unchanged
    assert original.system == original_system
    assert original.user == original_user
    assert original.projection == original_projection
    
    # Updated should have new values
    assert updated.system == system
    assert updated.user == user
    assert updated.projection == projection
    
    # Should be different objects
    assert updated is not original

# Property 5: Config JSON serialization filters nulls
@given(
    st.one_of(st.none(), st.text()),  # system
    st.one_of(st.none(), st.lists(st.text(), max_size=5)),  # user
    st.sampled_from([None, "surface", "normalized", "reading"]),  # projection
)
def test_config_json_filters_nulls(system, user, projection):
    """Test that Config.as_jsons() filters out None values."""
    config = Config(system=system, user=user, projection=projection)
    json_str = config.as_jsons()
    json_obj = json.loads(json_str)
    
    # None values should not be in the JSON
    if system is None:
        assert "system" not in json_obj
    else:
        assert json_obj.get("system") == system
        
    if user is None:
        assert "user" not in json_obj
    else:
        assert json_obj.get("user") == user
        
    if projection is None:
        assert "projection" not in json_obj
    else:
        assert json_obj.get("projection") == projection
    
    # JSON should be valid
    assert isinstance(json_obj, dict)

# Property 6: _find_dict_path validation
@given(st.text())
def test_find_dict_path_validation(dict_type):
    """Test that _find_dict_path only accepts 'small', 'core', or 'full'."""
    if dict_type in ['small', 'core', 'full']:
        # These should raise ModuleNotFoundError (since packages aren't installed)
        try:
            sudachipy._find_dict_path(dict_type)
            assert False, f"Expected ModuleNotFoundError for {dict_type}"
        except ModuleNotFoundError:
            pass  # Expected when package isn't installed
    else:
        # Invalid types should raise ValueError
        try:
            sudachipy._find_dict_path(dict_type)
            assert False, f"Expected ValueError for {repr(dict_type)}"
        except ValueError as e:
            assert '"dict_type" must be' in str(e)

# Property 7: Config projection field validation (based on documented values)
@given(st.text())
def test_config_projection_accepts_any_string(projection):
    """Test that Config accepts any string for projection field."""
    # The Config class doesn't validate projection values at creation time
    config = Config(projection=projection)
    assert config.projection == projection
    
    # Also test through update
    config2 = Config()
    updated = config2.update(projection=projection)
    assert updated.projection == projection

# Property 8: Multiple SplitMode creations are consistent
@given(st.sampled_from(['A', 'B', 'C']))
@settings(max_examples=100)
def test_splitmode_creation_consistency(mode_char):
    """Test that creating SplitMode multiple times gives consistent results."""
    modes = [SplitMode(mode_char) for _ in range(10)]
    
    # All should be equal
    assert all(m == modes[0] for m in modes)
    
    # And should equal the class attribute
    expected = getattr(SplitMode, mode_char)
    assert all(m == expected for m in modes)

# Property 9: Config default values match documentation
def test_config_defaults():
    """Test that Config default values match what's documented."""
    config = Config()
    
    # From the code and documentation
    assert config.system is None
    assert config.user is None
    assert config.projection == "surface"  # Default documented in pyi
    assert config.connectionCostPlugin is None
    assert config.oovProviderPlugin is None
    assert config.pathRewritePlugin is None
    assert config.inputTextPlugin is None
    assert config.characterDefinitionFile is None

if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])