#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import json
import math
from hypothesis import given, strategies as st, assume, settings, note
import sudachipy
from sudachipy import SplitMode, Config, errors

# Aggressive test 1: Config JSON with extreme values
@given(
    st.one_of(
        st.text(min_size=10000, max_size=100000),  # Very long strings
        st.text().map(lambda x: x * 1000),  # Repeated strings
        st.just("\\x00" * 100),  # Null bytes
        st.just("\n" * 1000),  # Many newlines
    )
)
@settings(max_examples=50)
def test_config_json_extreme_strings(extreme_string):
    """Test Config JSON serialization with extreme string values."""
    config = Config(system=extreme_string)
    json_str = config.as_jsons()
    
    # Should produce valid JSON
    parsed = json.loads(json_str)
    assert parsed["system"] == extreme_string
    
    # Test round-trip
    config2 = Config(system=parsed["system"])
    assert config2.system == extreme_string

# Aggressive test 2: Config with special JSON characters
@given(
    st.text(alphabet='"\\\b\f\n\r\t', min_size=1, max_size=100)
)
def test_config_json_escape_characters(special_chars):
    """Test Config JSON handles characters that need escaping."""
    config = Config(system=special_chars)
    json_str = config.as_jsons()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed["system"] == special_chars

# Aggressive test 3: Testing SplitMode with lookalike characters
@given(st.sampled_from([
    'Α', 'А', 'Ａ',  # Greek Alpha, Cyrillic A, Fullwidth A  
    'В', 'Ｂ',  # Cyrillic V, Fullwidth B
    'С', 'Ｃ',  # Cyrillic S, Fullwidth C
    'а', 'ａ',  # Cyrillic a, Fullwidth a
]))
def test_splitmode_unicode_lookalikes(lookalike):
    """Test SplitMode with Unicode characters that look like A/B/C."""
    try:
        result = SplitMode(lookalike)
        # If it accepts these, it might be doing visual matching incorrectly
        note(f"Accepted lookalike: {repr(lookalike)} -> {result}")
        assert False, f"Should not accept lookalike character {repr(lookalike)}"
    except errors.SudachiError:
        pass  # Expected

# Aggressive test 4: Config update with invalid types
@given(
    st.one_of(
        st.integers(),
        st.floats(allow_nan=True, allow_infinity=True),
        st.booleans(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text()),
    )
)
def test_config_type_coercion(value):
    """Test if Config handles type coercion or validation."""
    config = Config()
    
    # Try to set system to non-string value
    try:
        if isinstance(value, (int, float, bool)):
            # These might get coerced to strings
            updated = config.update(system=value)
            # Check if it was coerced
            assert isinstance(updated.system, (type(value), str))
        else:
            # Complex types should probably fail
            updated = config.update(system=value)
            # If this succeeds, check what happened
            assert updated.system == value
    except (TypeError, ValueError):
        # This is acceptable - rejecting invalid types
        pass

# Aggressive test 5: Config JSON with circular references (if possible)
def test_config_json_no_circular_refs():
    """Test that Config doesn't allow circular references."""
    config = Config()
    
    # Try to create a circular reference through user list
    circular_list = ["item1", "item2"]
    # Python lists can't have true circular references without custom objects
    # But we can test with self-referential structures
    
    config_with_list = Config(user=circular_list)
    json_str = config_with_list.as_jsons()
    parsed = json.loads(json_str)
    
    assert parsed.get("user") == circular_list

# Aggressive test 6: SplitMode with mixed case variations
@given(st.text(alphabet="AaBbCc", min_size=2, max_size=10))
def test_splitmode_mixed_case(mixed):
    """Test SplitMode with mixed case strings."""
    # Only single character A/B/C should work
    try:
        result = SplitMode(mixed)
        assert False, f"Should not accept multi-character string {repr(mixed)}"
    except errors.SudachiError:
        pass  # Expected

# Aggressive test 7: Testing integer overflow in Config lists
@given(st.lists(st.text(), min_size=1000, max_size=10000))
@settings(max_examples=10)
def test_config_huge_user_list(huge_list):
    """Test Config with very large user dictionary lists."""
    config = Config(user=huge_list)
    
    # Should handle large lists
    assert len(config.user) == len(huge_list)
    
    # JSON serialization should work
    json_str = config.as_jsons()
    parsed = json.loads(json_str)
    assert len(parsed["user"]) == len(huge_list)

# Aggressive test 8: Float values for projection
@given(st.floats())
def test_config_projection_float(float_val):
    """Test if Config projection field accepts floats."""
    try:
        config = Config(projection=float_val)
        # If it accepts floats, check the type
        assert config.projection == float_val or isinstance(config.projection, str)
    except (TypeError, ValueError):
        # Expected if it requires strings
        pass

# Aggressive test 9: Testing with byte strings
def test_splitmode_bytes():
    """Test SplitMode with byte strings."""
    for mode in [b'A', b'B', b'C', b'a', b'b', b'c']:
        try:
            result = SplitMode(mode)
            # If it accepts bytes, it's doing implicit conversion
            note(f"Accepted bytes: {mode} -> {result}")
        except (TypeError, errors.SudachiError):
            # Expected - should not accept bytes
            pass

# Aggressive test 10: Config with very nested structures
@given(
    st.recursive(
        st.text(min_size=1, max_size=10),
        lambda children: st.lists(children, min_size=1, max_size=3),
        max_leaves=100
    )
)
@settings(max_examples=20)
def test_config_nested_lists(nested):
    """Test Config with nested list structures."""
    try:
        config = Config(user=nested)
        # User field expects list of strings, not nested lists
        if any(isinstance(item, list) for item in nested):
            # This should probably fail or flatten
            json_str = config.as_jsons()
            parsed = json.loads(json_str)
            # Check what happened to the nested structure
            assert "user" in parsed
    except (TypeError, ValueError):
        # Expected if it validates structure
        pass

if __name__ == "__main__":
    import pytest  
    pytest.main([__file__, "-v", "-s", "--tb=short"])