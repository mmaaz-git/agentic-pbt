#!/usr/bin/env python3
"""
Property-based tests for sudachipy.tokenizer module components.
Testing components that don't require a dictionary.
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import json
from sudachipy import SplitMode, Config
from sudachipy.errors import SudachiError


# Test 1: SplitMode case insensitivity property
@given(st.sampled_from(["A", "B", "C"]))
def test_splitmode_case_insensitive(mode_char):
    """SplitMode should be case-insensitive according to documentation."""
    upper_mode = SplitMode(mode_char.upper())
    lower_mode = SplitMode(mode_char.lower())
    assert upper_mode == lower_mode, f"SplitMode('{mode_char.upper()}') != SplitMode('{mode_char.lower()}')"


# Test 2: SplitMode None defaults to C
@given(st.none())
def test_splitmode_none_defaults_to_c(none_value):
    """SplitMode(None) should default to SplitMode.C as documented."""
    mode = SplitMode(none_value)
    assert mode == SplitMode.C, f"SplitMode(None) returned {mode}, expected SplitMode.C"


# Test 3: SplitMode only accepts valid values
@given(st.text(min_size=1))
def test_splitmode_invalid_input_rejection(text):
    """SplitMode should only accept 'A', 'B', 'C' (case insensitive)."""
    # Filter out valid inputs
    assume(text.upper() not in ["A", "B", "C"])
    
    try:
        mode = SplitMode(text)
        # If we get here, it accepted an invalid input
        assert False, f"SplitMode incorrectly accepted '{text}' as valid input, returned {mode}"
    except SudachiError:
        # Expected behavior - invalid inputs should raise SudachiError
        pass
    except TypeError:
        # Also acceptable for non-string inputs
        pass


# Test 4: SplitMode singleton behavior
@given(st.sampled_from(["A", "B", "C", "a", "b", "c"]))
def test_splitmode_equality_consistency(mode_str):
    """Multiple SplitMode creations with same input should be equal."""
    mode1 = SplitMode(mode_str)
    mode2 = SplitMode(mode_str)
    assert mode1 == mode2, f"SplitMode('{mode_str}') created unequal instances"
    
    # Also test against the class constants
    expected = getattr(SplitMode, mode_str.upper())
    assert mode1 == expected, f"SplitMode('{mode_str}') != SplitMode.{mode_str.upper()}"


# Test 5: Config default values preservation
@given(st.none())
def test_config_default_projection(none_val):
    """Config should have 'surface' as default projection value."""
    config = Config()
    assert config.projection == 'surface', f"Default projection is '{config.projection}', expected 'surface'"


# Test 6: Config initialization with custom values
@given(
    system=st.one_of(st.none(), st.text()),
    projection=st.sampled_from(['surface', 'normalized', 'reading', 'dictionary'])
)
def test_config_initialization(system, projection):
    """Config should preserve initialization parameters."""
    config = Config(system=system, projection=projection)
    assert config.system == system, f"Config.system={config.system}, expected {system}"
    assert config.projection == projection, f"Config.projection={config.projection}, expected {projection}"


# Test 7: Config.as_jsons round-trip property
@given(
    projection=st.sampled_from(['surface', 'normalized', 'reading', 'dictionary']),
    character_def=st.one_of(st.none(), st.text(min_size=1))
)
def test_config_json_serialization(projection, character_def):
    """Config should be JSON-serializable via as_jsons method."""
    config = Config(projection=projection, characterDefinitionFile=character_def)
    
    # Serialize to JSON
    json_str = config.as_jsons()
    
    # Should be valid JSON
    try:
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict), "Config.as_jsons() should produce a JSON object"
        
        # Check that values are preserved in JSON
        if projection != 'surface':  # surface is default, might not be in JSON
            assert parsed.get('projection') == projection, f"projection not preserved in JSON"
        if character_def is not None:
            assert parsed.get('characterDefinitionFile') == character_def, f"characterDefinitionFile not preserved in JSON"
    except json.JSONDecodeError as e:
        assert False, f"Config.as_jsons() produced invalid JSON: {e}"


# Test 8: Config.update returns new immutable Config
@given(
    initial_projection=st.sampled_from(['surface', 'normalized']),
    update_system=st.text(min_size=1),
    update_projection=st.sampled_from(['reading', 'dictionary'])
)
def test_config_update_immutability(initial_projection, update_system, update_projection):
    """Config.update should return a new Config with updates, not modify original."""
    original = Config(projection=initial_projection)
    
    # Update config - returns new instance
    updated = original.update(system=update_system, projection=update_projection)
    
    # Original should be unchanged (immutability)
    assert original.projection == initial_projection, f"Original config was modified!"
    assert original.system is None, f"Original config system was modified!"
    
    # Updated should have new values
    assert updated.system == update_system, f"Updated config system not set"
    assert updated.projection == update_projection, f"Updated config projection not set"
    
    # Should be different objects
    assert original is not updated, "update() returned same object instead of new one"


# Test 9: Config.update with empty args returns copy
@given(
    projection=st.sampled_from(['surface', 'normalized', 'reading']),
    system=st.one_of(st.none(), st.text())
)
def test_config_update_empty_returns_copy(projection, system):
    """Config.update() with no arguments should return a copy with same values."""
    original = Config(projection=projection, system=system)
    copy = original.update()
    
    # Should have same values
    assert copy.projection == original.projection
    assert copy.system == original.system
    
    # Should be different objects
    assert copy is not original


# Test 10: All SplitMode constants are distinct
def test_splitmode_constants_distinct():
    """SplitMode.A, B, and C should all be distinct."""
    modes = [SplitMode.A, SplitMode.B, SplitMode.C]
    for i, mode1 in enumerate(modes):
        for j, mode2 in enumerate(modes):
            if i != j:
                assert mode1 != mode2, f"SplitMode.{chr(65+i)} == SplitMode.{chr(65+j)}"


# Test 11: Empty string handling for SplitMode
@given(st.just(""))
def test_splitmode_empty_string(empty):
    """SplitMode should reject empty strings."""
    try:
        mode = SplitMode(empty)
        assert False, f"SplitMode accepted empty string, returned {mode}"
    except SudachiError:
        # Expected - empty string is invalid
        pass


if __name__ == "__main__":
    print("Running property-based tests for sudachipy.tokenizer components...")
    print("=" * 60)
    
    # Run tests with pytest if available, otherwise run directly
    try:
        import pytest
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        # Run tests manually
        import traceback
        
        test_functions = [
            test_splitmode_case_insensitive,
            test_splitmode_none_defaults_to_c,
            test_splitmode_invalid_input_rejection,
            test_splitmode_equality_consistency,
            test_config_default_projection,
            test_config_initialization,
            test_config_json_serialization,
            test_config_update_immutability,
            test_config_update_empty_returns_copy,
            test_splitmode_constants_distinct,
            test_splitmode_empty_string
        ]
        
        for test_func in test_functions:
            try:
                print(f"Running {test_func.__name__}...")
                test_func()
                print(f"  ✓ Passed")
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                traceback.print_exc()
        
        print("\nNote: Install pytest for better test output")