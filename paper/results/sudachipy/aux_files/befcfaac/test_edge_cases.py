#!/usr/bin/env python3
"""
Edge case testing for sudachipy.tokenizer components.
Looking for potential bugs in boundary conditions.
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import json
from sudachipy import SplitMode, Config
from sudachipy.errors import SudachiError


# Test edge cases for SplitMode with unicode and special characters
@given(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cf')), min_size=1, max_size=10))
def test_splitmode_unicode_handling(text):
    """SplitMode should properly reject non-ABC unicode strings."""
    # Skip if it's actually a valid mode
    assume(text.upper() not in ["A", "B", "C"])
    
    try:
        mode = SplitMode(text)
        assert False, f"SplitMode accepted '{text}' (len={len(text)}, repr={repr(text)})"
    except (SudachiError, TypeError):
        # Expected - should reject
        pass


# Test Config with extreme values
@given(
    system=st.one_of(
        st.none(),
        st.text(min_size=0, max_size=10000),  # Very long strings
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cf')))  # Unicode
    ),
    projection=st.one_of(
        st.sampled_from(['surface', 'normalized', 'reading', 'dictionary']),
        st.text(min_size=1)  # Invalid projection values
    )
)
def test_config_extreme_values(system, projection):
    """Config should handle extreme input values gracefully."""
    try:
        config = Config(system=system, projection=projection)
        
        # Check values are preserved
        assert config.system == system
        assert config.projection == projection
        
        # Should be JSON serializable even with extreme values
        json_str = config.as_jsons()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        
    except (ValueError, TypeError) as e:
        # Some invalid projections might be rejected
        if projection not in ['surface', 'normalized', 'reading', 'dictionary']:
            pass  # Expected for invalid projection values
        else:
            raise  # Unexpected error for valid values


# Test Config.update with many simultaneous updates
@given(
    st.dictionaries(
        keys=st.sampled_from(['system', 'projection', 'characterDefinitionFile']),
        values=st.one_of(st.none(), st.text()),
        min_size=0,
        max_size=3
    )
)
def test_config_update_multiple_fields(updates):
    """Config.update should handle multiple field updates correctly."""
    original = Config()
    
    # Convert dict to kwargs
    updated = original.update(**updates)
    
    # Check all updates were applied
    for key, value in updates.items():
        assert getattr(updated, key) == value, f"Field {key} not updated correctly"
    
    # Original should be unchanged
    assert original.system is None
    assert original.projection == 'surface'


# Test repeated updates (immutability chain)
@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_config_update_chain(systems):
    """Chained Config.update calls should work correctly."""
    config = Config()
    
    for i, system in enumerate(systems):
        config = config.update(system=system)
        assert config.system == system, f"Update {i} failed"
    
    # Final config should have last system
    assert config.system == systems[-1]


# Test SplitMode with whitespace variations
@given(st.sampled_from([" A", "A ", " A ", "\tA", "A\n", "\nA\t"]))
def test_splitmode_whitespace(mode_with_space):
    """SplitMode should handle strings with whitespace."""
    try:
        mode = SplitMode(mode_with_space)
        # If it accepts whitespace, it should still resolve to the correct mode
        assert mode == SplitMode.A, f"Whitespace handling produced wrong mode: {mode}"
    except SudachiError:
        # Also acceptable - rejecting whitespace
        pass


# Test Config JSON serialization with None values
@given(st.booleans())
def test_config_json_none_handling(include_none):
    """Config.as_jsons should handle None values properly."""
    if include_none:
        config = Config(system=None, projection='surface')
    else:
        config = Config(system='test', projection='surface')
    
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    
    # None values might be omitted or included as null
    if include_none:
        # system=None might not appear in JSON or might be null
        assert parsed.get('system') in [None, 'null'] or 'system' not in parsed
    else:
        assert parsed.get('system') == 'test'


# Test Config with empty strings
@given(st.just(""))
def test_config_empty_string_system(empty):
    """Config should handle empty string as system value."""
    config = Config(system=empty)
    assert config.system == ""
    
    # Should be JSON serializable
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    assert parsed.get('system') == ""


# Test SplitMode case variations
@given(st.sampled_from(["A", "a", "B", "b", "C", "c"]))
def test_splitmode_case_preservation(mode_str):
    """SplitMode should normalize case internally."""
    mode = SplitMode(mode_str)
    # String representation should be uppercase
    str_repr = str(mode)
    assert mode_str.upper() in str_repr, f"Mode string representation doesn't contain uppercase letter"


# Test Config.update preserves unspecified fields
@given(
    projection=st.sampled_from(['surface', 'normalized']),
    system=st.text(min_size=1),
    char_def=st.text(min_size=1)
)
def test_config_update_partial(projection, system, char_def):
    """Config.update should preserve fields not being updated."""
    config = Config(
        projection=projection,
        system=system,
        characterDefinitionFile=char_def
    )
    
    # Update only projection
    updated = config.update(projection='reading')
    
    # Check projection was updated
    assert updated.projection == 'reading'
    
    # Check other fields preserved
    assert updated.system == system
    assert updated.characterDefinitionFile == char_def


# Test Config list fields
@given(st.lists(st.text(), min_size=0, max_size=5))
def test_config_user_list(user_list):
    """Config should handle list fields like 'user' correctly."""
    config = Config(user=user_list)
    assert config.user == user_list
    
    # Should be JSON serializable
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    
    if user_list:  # Non-empty lists should be in JSON
        assert parsed.get('user') == user_list


if __name__ == "__main__":
    print("Running edge case tests...")
    print("=" * 60)
    
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])