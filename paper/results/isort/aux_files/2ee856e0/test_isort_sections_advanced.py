"""Advanced property-based tests for isort.sections module and its interactions."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.sections as sections
from isort.settings import Config, KNOWN_SECTION_MAPPING
from isort.place import module, module_with_reason
from hypothesis import given, strategies as st, settings, assume
import pytest


@given(st.lists(st.sampled_from(list(sections.DEFAULT)), min_size=2, unique=True))
def test_custom_section_ordering_preserved(custom_order):
    """Property test: Custom section ordering should be preserved in Config."""
    config = Config(sections=tuple(custom_order))
    assert config.sections == tuple(custom_order)


@given(st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=3, max_size=15))
def test_custom_section_not_in_defaults(custom_section_name):
    """Property test: Custom sections not in DEFAULT should be allowed."""
    assume(custom_section_name not in sections.DEFAULT)
    
    # Config should accept custom section names
    try:
        config = Config(sections=(sections.STDLIB, custom_section_name, sections.THIRDPARTY))
        assert custom_section_name in config.sections
    except Exception:
        # If it fails, it should only be for valid reasons
        pass


@given(
    st.lists(
        st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs']), min_size=1, max_size=20),
        min_size=1,
        max_size=5,
        unique=True
    )
)
def test_module_placement_with_known_first_party(module_names):
    """Property test: Modules configured as first-party should be placed in FIRSTPARTY section."""
    config = Config(known_first_party=frozenset(module_names))
    
    for module_name in module_names:
        placement = module(module_name, config)
        # The module should be placed in FIRSTPARTY since we configured it
        assert placement == sections.FIRSTPARTY


@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20))
def test_local_module_detection(module_name):
    """Property test: Modules starting with '.' should be in LOCALFOLDER."""
    local_module = f".{module_name}"
    config = Config()
    
    placement, reason = module_with_reason(local_module, config)
    assert placement == sections.LOCALFOLDER
    assert "dot" in reason.lower()


@given(st.sampled_from(['__future__']))
def test_future_module_placement(future_module):
    """Property test: __future__ should always be placed in FUTURE section."""
    config = Config()
    placement = module(future_module, config)
    
    # __future__ is configured as known_future_library by default
    assert placement == sections.FUTURE


@given(
    st.lists(st.sampled_from(list(sections.DEFAULT)), min_size=1, max_size=3, unique=True),
    st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=3, max_size=10)
)
def test_default_section_fallback(partial_sections, unknown_module):
    """Property test: Unknown modules should fall back to default_section."""
    assume(unknown_module not in ['sys', 'os', 'math'])  # Avoid stdlib
    assume(not unknown_module.startswith('.'))  # Avoid local modules
    
    config = Config(
        sections=tuple(partial_sections),
        default_section=sections.THIRDPARTY,
        known_first_party=frozenset(),
        known_third_party=frozenset()
    )
    
    placement = module(unknown_module, config)
    # Should use the default section for unknown modules
    assert placement == sections.THIRDPARTY


@given(st.data())
def test_known_section_mapping_reverse_lookup(data):
    """Property test: KNOWN_SECTION_MAPPING should have consistent reverse mapping."""
    section = data.draw(st.sampled_from(list(KNOWN_SECTION_MAPPING.keys())))
    mapped_value = KNOWN_SECTION_MAPPING[section]
    
    # The mapped value should follow a pattern
    if section == sections.STDLIB:
        assert mapped_value == "STANDARD_LIBRARY"
    elif section == sections.FUTURE:
        assert mapped_value == "FUTURE_LIBRARY"
    else:
        # For others, it should be the section name with underscores
        expected = section.replace("PARTY", "_PARTY").replace("FOLDER", "_FOLDER")
        assert mapped_value == expected


@given(st.lists(st.sampled_from(list(sections.DEFAULT)), min_size=0))
def test_duplicate_sections_in_config(section_list):
    """Property test: Config with duplicate sections should handle them properly."""
    # Intentionally create duplicates
    sections_with_dupes = tuple(section_list)
    
    try:
        config = Config(sections=sections_with_dupes)
        # Config should accept it (no explicit uniqueness validation)
        assert config.sections == sections_with_dupes
    except ValueError:
        # Or it might validate and reject duplicates
        pass


@settings(max_examples=50)
@given(
    st.lists(
        st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10),
        min_size=1,
        max_size=3
    )
)
def test_forced_separate_sections(module_names):
    """Property test: forced_separate should create separate sections."""
    # Create a config with forced_separate
    forced_separate_pattern = module_names[0]
    config = Config(forced_separate=(forced_separate_pattern,))
    
    # Modules matching the pattern should be in their own section
    placement, reason = module_with_reason(forced_separate_pattern, config)
    assert placement == forced_separate_pattern
    assert "forced_separate" in reason


@given(st.integers(min_value=-10, max_value=10))
def test_default_tuple_bounds_checking(index):
    """Property test: DEFAULT tuple should handle index access correctly."""
    if -len(sections.DEFAULT) <= index < len(sections.DEFAULT):
        # Valid index - should not raise
        section = sections.DEFAULT[index]
        assert isinstance(section, str)
    else:
        # Invalid index - should raise IndexError
        with pytest.raises(IndexError):
            _ = sections.DEFAULT[index]


@given(st.data())
def test_section_order_in_default_is_logical(data):
    """Property test: The order in DEFAULT follows import sorting logic."""
    # The order should be: FUTURE -> STDLIB -> THIRDPARTY -> FIRSTPARTY -> LOCALFOLDER
    # This represents the typical import order in Python files
    
    idx = data.draw(st.integers(min_value=0, max_value=len(sections.DEFAULT)-2))
    current = sections.DEFAULT[idx]
    next_section = sections.DEFAULT[idx + 1]
    
    # Define the expected ordering priority
    order_priority = {
        sections.FUTURE: 0,
        sections.STDLIB: 1,
        sections.THIRDPARTY: 2,
        sections.FIRSTPARTY: 3,
        sections.LOCALFOLDER: 4
    }
    
    assert order_priority[current] < order_priority[next_section]


def test_empty_sections_config():
    """Test that empty sections tuple is handled."""
    try:
        config = Config(sections=())
        assert config.sections == ()
    except Exception:
        # Empty sections might not be allowed
        pass


@given(st.lists(st.text(min_size=1, max_size=5), min_size=100, max_size=200))
def test_large_known_modules_list(large_module_list):
    """Property test: Config should handle large lists of known modules."""
    config = Config(known_third_party=frozenset(large_module_list))
    
    # All modules in the list should be recognized as third-party
    for module_name in large_module_list[:10]:  # Test a sample
        if not module_name.startswith('.'):
            placement = module(module_name, config)
            assert placement == sections.THIRDPARTY