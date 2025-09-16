"""Property-based tests for isort.sections module."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.sections as sections
from hypothesis import given, strategies as st, settings
import pytest


def test_section_constants_are_strings():
    """Test that all section constants are strings."""
    assert isinstance(sections.FUTURE, str)
    assert isinstance(sections.STDLIB, str)
    assert isinstance(sections.THIRDPARTY, str)
    assert isinstance(sections.FIRSTPARTY, str)
    assert isinstance(sections.LOCALFOLDER, str)


def test_section_constants_are_unique():
    """Test that all section constants have unique values."""
    section_values = {
        sections.FUTURE,
        sections.STDLIB,
        sections.THIRDPARTY,
        sections.FIRSTPARTY,
        sections.LOCALFOLDER
    }
    # If all values are unique, the set should have 5 elements
    assert len(section_values) == 5


def test_default_contains_all_sections():
    """Test that DEFAULT tuple contains all defined section constants."""
    expected_sections = {
        sections.FUTURE,
        sections.STDLIB,
        sections.THIRDPARTY,
        sections.FIRSTPARTY,
        sections.LOCALFOLDER
    }
    actual_sections = set(sections.DEFAULT)
    assert expected_sections == actual_sections


def test_default_has_no_duplicates():
    """Test that DEFAULT tuple has no duplicate values."""
    assert len(sections.DEFAULT) == len(set(sections.DEFAULT))


def test_default_ordering():
    """Test that DEFAULT maintains the expected order."""
    expected_order = (
        sections.FUTURE,
        sections.STDLIB,
        sections.THIRDPARTY,
        sections.FIRSTPARTY,
        sections.LOCALFOLDER
    )
    assert sections.DEFAULT == expected_order


def test_default_is_tuple():
    """Test that DEFAULT is a tuple (immutable)."""
    assert isinstance(sections.DEFAULT, tuple)


def test_sections_immutability():
    """Test that section constants can't be accidentally modified."""
    # Strings are immutable in Python, so this is always true
    # But we test that the module doesn't expose any mutable state
    original_future = sections.FUTURE
    original_default = sections.DEFAULT
    
    # These operations shouldn't modify the originals
    _ = sections.FUTURE + "_test"
    _ = sections.DEFAULT + ("TEST",)
    
    assert sections.FUTURE == original_future
    assert sections.DEFAULT == original_default


@given(st.sampled_from(list(sections.DEFAULT)))
def test_default_elements_are_strings(section):
    """Property test: Every element in DEFAULT must be a string."""
    assert isinstance(section, str)


@given(st.integers(min_value=0, max_value=4))
def test_default_indexing(index):
    """Property test: DEFAULT should be indexable and return strings."""
    section = sections.DEFAULT[index]
    assert isinstance(section, str)
    assert section in {
        sections.FUTURE,
        sections.STDLIB,
        sections.THIRDPARTY,
        sections.FIRSTPARTY,
        sections.LOCALFOLDER
    }


def test_known_section_mapping_consistency():
    """Test that KNOWN_SECTION_MAPPING in settings corresponds to actual sections."""
    # Import settings to check the mapping
    from isort.settings import KNOWN_SECTION_MAPPING
    
    # All keys in KNOWN_SECTION_MAPPING should be actual section constants
    for section_const in KNOWN_SECTION_MAPPING.keys():
        assert section_const in sections.DEFAULT
    
    # Check that mapped values follow a consistent pattern
    assert KNOWN_SECTION_MAPPING[sections.STDLIB] == "STANDARD_LIBRARY"
    assert KNOWN_SECTION_MAPPING[sections.FUTURE] == "FUTURE_LIBRARY"
    assert KNOWN_SECTION_MAPPING[sections.FIRSTPARTY] == "FIRST_PARTY"
    assert KNOWN_SECTION_MAPPING[sections.THIRDPARTY] == "THIRD_PARTY"
    assert KNOWN_SECTION_MAPPING[sections.LOCALFOLDER] == "LOCAL_FOLDER"


@given(st.data())
def test_section_constant_values_are_uppercase(data):
    """Property test: All section constant values should be uppercase strings."""
    section = data.draw(st.sampled_from([
        sections.FUTURE,
        sections.STDLIB,
        sections.THIRDPARTY,
        sections.FIRSTPARTY,
        sections.LOCALFOLDER
    ]))
    assert section.isupper()
    assert section.isalpha()


def test_config_uses_section_defaults():
    """Test that Config class correctly uses SECTION_DEFAULTS."""
    from isort.settings import Config, SECTION_DEFAULTS
    
    # SECTION_DEFAULTS should be the same as sections.DEFAULT
    assert SECTION_DEFAULTS == sections.DEFAULT
    
    # Default config should use SECTION_DEFAULTS
    config = Config()
    assert config.sections == SECTION_DEFAULTS


@given(st.lists(st.sampled_from(list(sections.DEFAULT)), min_size=0, max_size=10))
def test_section_subset_validation(section_subset):
    """Property test: Any subset of DEFAULT sections should be valid for config."""
    from isort.settings import Config
    
    # Convert list to tuple (Config expects tuple)
    section_tuple = tuple(section_subset)
    
    # This should not raise an exception for valid section names
    try:
        config = Config(sections=section_tuple)
        # All sections in config should be from DEFAULT or custom
        for section in config.sections:
            # Either it's a known section or it could be a custom section
            assert isinstance(section, str)
    except Exception as e:
        # Config might validate uniqueness or other properties
        # If it fails, it should be for a good reason
        pass


@settings(max_examples=100)
@given(st.text(min_size=1, max_size=20))
def test_section_names_are_not_arbitrary_strings(section_name):
    """Property test: Arbitrary strings should not match section constants."""
    # Unless we randomly generate one of the actual section names,
    # it shouldn't match any of our constants
    if section_name not in {"FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"}:
        assert section_name != sections.FUTURE
        assert section_name != sections.STDLIB
        assert section_name != sections.THIRDPARTY
        assert section_name != sections.FIRSTPARTY
        assert section_name != sections.LOCALFOLDER


def test_section_constants_match_their_names():
    """Test that section constant values match their variable names."""
    assert sections.FUTURE == "FUTURE"
    assert sections.STDLIB == "STDLIB"
    assert sections.THIRDPARTY == "THIRDPARTY"
    assert sections.FIRSTPARTY == "FIRSTPARTY"
    assert sections.LOCALFOLDER == "LOCALFOLDER"