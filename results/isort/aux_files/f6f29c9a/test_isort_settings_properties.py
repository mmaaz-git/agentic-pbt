"""Property-based tests for isort.settings module using Hypothesis."""

import sys
import os
from pathlib import Path

# Add the isort package to the path
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import pytest
from hypothesis import assume, given, settings, strategies as st
from isort.settings import (
    _as_bool,
    _as_list,
    _abspaths,
    Config,
    _Config,
    VALID_PY_TARGETS,
    _STR_BOOLEAN_MAPPING,
)


# Property 1: _as_bool function - bidirectional mapping property
# Evidence: Lines 931-938 show it uses _STR_BOOLEAN_MAPPING dictionary
@given(st.sampled_from(list(_STR_BOOLEAN_MAPPING.keys())))
def test_as_bool_valid_inputs(input_str):
    """Test that _as_bool correctly maps all defined string values."""
    result = _as_bool(input_str)
    assert isinstance(result, bool)
    assert result == _STR_BOOLEAN_MAPPING[input_str]
    
    # Also test uppercase versions should work (line 936 shows .lower() is used)
    result_upper = _as_bool(input_str.upper())
    assert result_upper == result


@given(st.text().filter(lambda x: x.lower() not in _STR_BOOLEAN_MAPPING))
def test_as_bool_invalid_inputs(input_str):
    """Test that _as_bool raises ValueError for undefined inputs."""
    with pytest.raises(ValueError, match=f"invalid truth value"):
        _as_bool(input_str)


# Property 2: _as_list function - idempotence property
# Evidence: Lines 753-757 show it handles both string and list inputs
@given(st.lists(st.text()))
def test_as_list_idempotent_for_lists(input_list):
    """Test that _as_list is idempotent when given a list."""
    result1 = _as_list(input_list)
    result2 = _as_list(result1)
    assert result1 == result2


@given(st.text())
def test_as_list_string_splitting(input_str):
    """Test that _as_list correctly splits strings on commas and newlines."""
    result = _as_list(input_str)
    assert isinstance(result, list)
    
    # The function strips whitespace and filters empty items
    for item in result:
        assert item == item.strip()
        assert len(item) > 0


# Property 3: _as_list round-trip property for comma-separated strings
@given(st.lists(st.text(alphabet=st.characters(blacklist_characters=",\n"), min_size=1), min_size=1))
def test_as_list_round_trip(strings):
    """Test round-trip: list -> comma-joined -> _as_list -> list."""
    # Create a comma-separated string
    comma_string = ", ".join(strings)
    
    # Parse it back
    result = _as_list(comma_string)
    
    # Should get back the original strings (stripped)
    expected = [s.strip() for s in strings]
    assert result == expected


# Property 4: Config wrap_length validation
# Evidence: Lines 280-284 show wrap_length must be <= line_length
@given(
    line_length=st.integers(min_value=1, max_value=1000),
    wrap_length=st.integers(min_value=0, max_value=2000)
)
def test_config_wrap_length_validation(line_length, wrap_length):
    """Test that Config enforces wrap_length <= line_length."""
    if wrap_length > line_length:
        with pytest.raises(ValueError, match="wrap_length must be set lower than or equal to line_length"):
            Config(line_length=line_length, wrap_length=wrap_length)
    else:
        # Should not raise
        config = Config(line_length=line_length, wrap_length=wrap_length)
        assert config.wrap_length == wrap_length
        assert config.line_length == line_length


# Property 5: py_version validation
# Evidence: Lines 257-262 show it only accepts valid Python versions
@given(st.text())
def test_py_version_validation(py_version):
    """Test that Config only accepts valid Python versions."""
    if py_version == "auto" or py_version in VALID_PY_TARGETS:
        # Should not raise for valid versions
        config = Config(py_version=py_version)
        if py_version != "all" and py_version != "auto":
            assert config.py_version == f"py{py_version}"
    else:
        # Should raise for invalid versions
        with pytest.raises(ValueError, match="The python version .* is not supported"):
            Config(py_version=py_version)


# Property 6: skips property combines skip and extend_skip
# Evidence: Lines 696-697 show skips = skip.union(extend_skip)
@given(
    skip=st.frozensets(st.text(min_size=1)),
    extend_skip=st.frozensets(st.text(min_size=1))
)
def test_skips_union_property(skip, extend_skip):
    """Test that the skips property is the union of skip and extend_skip."""
    config = Config(skip=skip, extend_skip=extend_skip)
    
    # The skips property should be the union
    assert config.skips == skip.union(extend_skip)
    
    # All items from both sets should be in skips
    for item in skip:
        assert item in config.skips
    for item in extend_skip:
        assert item in config.skips


# Property 7: skip_globs property combines skip_glob and extend_skip_glob
# Evidence: Lines 704-705 show skip_globs = skip_glob.union(extend_skip_glob)
@given(
    skip_glob=st.frozensets(st.text(min_size=1)),
    extend_skip_glob=st.frozensets(st.text(min_size=1))
)
def test_skip_globs_union_property(skip_glob, extend_skip_glob):
    """Test that the skip_globs property is the union of skip_glob and extend_skip_glob."""
    config = Config(skip_glob=skip_glob, extend_skip_glob=extend_skip_glob)
    
    # The skip_globs property should be the union
    assert config.skip_globs == skip_glob.union(extend_skip_glob)
    
    # All items from both sets should be in skip_globs
    for item in skip_glob:
        assert item in config.skip_globs
    for item in extend_skip_glob:
        assert item in config.skip_globs


# Property 8: _abspaths function behavior
# Evidence: Lines 760-769 show it converts relative paths to absolute paths
@given(
    cwd=st.text(min_size=1).map(lambda x: f"/test/{x}"),
    values=st.lists(st.text(min_size=1))
)
def test_abspaths_conversion(cwd, values):
    """Test that _abspaths correctly handles path conversion."""
    result = _abspaths(cwd, values)
    
    assert isinstance(result, set)
    
    for value in values:
        # Check that paths ending with separator and not starting with separator
        # get joined with cwd (line 764)
        if not value.startswith(os.path.sep) and value.endswith(os.path.sep):
            expected = os.path.join(cwd, value)
            assert expected in result or value in result
        else:
            assert value in result


# Property 9: force_alphabetical_sort implications
# Evidence: Lines 275-279 show force_alphabetical_sort sets multiple other options
@given(st.booleans())
def test_force_alphabetical_sort_implications(force_alphabetical):
    """Test that force_alphabetical_sort correctly sets related options."""
    config = Config(force_alphabetical_sort=force_alphabetical)
    
    if force_alphabetical:
        # These should all be set when force_alphabetical_sort is True
        assert config.force_alphabetical_sort_within_sections == True
        assert config.no_sections == True
        assert config.lines_between_types == 1
        assert config.from_first == True


# Property 10: Config properties are cached
# Evidence: Lines 652-673, 676-681, etc. show properties are cached with _known_patterns check
def test_config_property_caching():
    """Test that Config properties are properly cached."""
    config = Config()
    
    # First access
    patterns1 = config.known_patterns
    # Second access should return the same object (cached)
    patterns2 = config.known_patterns
    assert patterns1 is patterns2
    
    # Same for section_comments
    comments1 = config.section_comments
    comments2 = config.section_comments
    assert comments1 is comments2


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])