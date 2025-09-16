#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings, example
import sudachipy
from sudachipy import SplitMode, Config, errors

# Edge case 1: Unicode and special characters in SplitMode
@given(st.text(min_size=1).filter(lambda s: any(c in 'AaBbCc' for c in s)))
def test_splitmode_with_extra_characters(text_with_abc):
    """Test SplitMode behavior with strings containing valid mode chars plus extra characters."""
    # Should still raise error if not exactly 'A', 'B', or 'C'
    if text_with_abc.upper() not in ['A', 'B', 'C']:
        try:
            SplitMode(text_with_abc)
            assert False, f"Should have raised error for {repr(text_with_abc)}"
        except errors.SudachiError:
            pass  # Expected

# Edge case 2: Config with very large lists
@given(st.lists(st.text(min_size=1, max_size=1000), min_size=15, max_size=20))
def test_config_user_dict_limit(large_user_list):
    """Test that Config handles user dictionary limit (max 14 according to pyi)."""
    # The pyi documentation says maximum 14 user dictionaries
    config = Config(user=large_user_list)
    # Config accepts it without validation
    assert config.user == large_user_list
    # This might be a documentation vs implementation mismatch

# Edge case 3: Config JSON with special characters
@given(
    st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), min_codepoint=1)),
    st.lists(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), min_codepoint=1)), max_size=3)
)
def test_config_json_unicode_handling(system, user):
    """Test Config JSON serialization with various unicode characters."""
    config = Config(system=system, user=user)
    json_str = config.as_jsons()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Values should round-trip correctly
    if system is not None:
        assert parsed.get("system") == system
    if user is not None:
        assert parsed.get("user") == user

# Edge case 4: Empty string handling
@given(st.just(""))
def test_splitmode_empty_string(empty):
    """Test SplitMode with empty string."""
    try:
        SplitMode(empty)
        assert False, "Should raise error for empty string"
    except errors.SudachiError as e:
        assert "Mode must be one of" in str(e)

# Edge case 5: Whitespace handling  
@given(st.sampled_from([" A", "A ", " A ", "\tB", "C\n", " a ", "\ta\t"]))
def test_splitmode_whitespace(mode_with_whitespace):
    """Test if SplitMode handles whitespace around valid modes."""
    try:
        result = SplitMode(mode_with_whitespace)
        # If it succeeds, it might be stripping whitespace
        stripped = mode_with_whitespace.strip()
        if stripped.upper() in ['A', 'B', 'C']:
            expected = getattr(SplitMode, stripped.upper())
            print(f"SplitMode({repr(mode_with_whitespace)}) = {result}, expected = {expected}")
    except errors.SudachiError:
        # This is expected if it doesn't strip whitespace
        pass

# Edge case 6: Config with recursive data structures  
def test_config_json_with_none_values():
    """Test that all-None config still produces valid JSON."""
    config = Config(
        system=None,
        user=None, 
        projection=None,
        connectionCostPlugin=None,
        oovProviderPlugin=None,
        pathRewritePlugin=None,
        inputTextPlugin=None,
        characterDefinitionFile=None
    )
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    
    # Should produce minimal JSON
    assert isinstance(parsed, dict)
    # None values should be filtered out
    assert "system" not in parsed
    assert "user" not in parsed
    
# Edge case 7: Integer strings for SplitMode
@given(st.integers())
def test_splitmode_integer_input(number):
    """Test SplitMode with integer inputs converted to strings."""
    str_num = str(number)
    try:
        SplitMode(str_num)
        assert False, f"Should raise error for {repr(str_num)}"
    except errors.SudachiError:
        pass  # Expected

# Edge case 8: Config field that shouldn't exist
def test_config_arbitrary_fields():
    """Test if Config accepts arbitrary fields through update()."""
    config = Config()
    try:
        # Try to add a field that doesn't exist
        updated = config.update(nonexistent_field="test")
        # If this succeeds, it's accepting arbitrary fields
        assert False, "Config.update() accepted non-existent field"
    except TypeError:
        # This is expected - dataclass should reject unknown fields
        pass

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])