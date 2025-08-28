"""Property-based tests for copier._template module."""

import sys
import os
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

import pytest
from hypothesis import given, strategies as st, assume, settings
from packaging.version import Version, InvalidVersion

# Add the copier module to path
sys.path.insert(0, "/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages")

from copier._template import (
    filter_config,
    verify_copier_version,
    Template,
    load_template_config,
)
from copier.errors import UnsupportedVersionError, InvalidConfigFileError


# Property 1: filter_config separates configuration and questions correctly
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.booleans(),
            st.dictionaries(st.text(), st.text()),
        ),
        min_size=0,
        max_size=20,
    )
)
def test_filter_config_separation(data):
    """Test that filter_config correctly separates config and questions data."""
    config_data, questions_data = filter_config(data)
    
    # All keys starting with "_" should be in config_data (without the underscore)
    for key in data:
        if key.startswith("_"):
            assert key[1:] in config_data
            assert key not in questions_data
            assert config_data[key[1:]] == data[key]
        else:
            # Non-underscore keys should be in questions_data
            assert key in questions_data
            assert key not in config_data
            
            # Questions should be normalized to dict format
            assert isinstance(questions_data[key], dict)
            if isinstance(data[key], dict):
                assert questions_data[key] == data[key]
            else:
                # Simple values should be wrapped in dict with "default" key
                assert questions_data[key] == {"default": data[key]}
    
    # No keys should be lost or added
    config_keys = set("_" + k for k in config_data.keys())
    question_keys = set(questions_data.keys())
    original_keys = set(data.keys())
    
    underscore_keys = {k for k in original_keys if k.startswith("_")}
    non_underscore_keys = {k for k in original_keys if not k.startswith("_")}
    
    assert config_keys == underscore_keys
    assert question_keys == non_underscore_keys


# Property 2: Round-trip property for filter_config
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: not x.startswith("_")),
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.booleans(),
        ),
        min_size=0,
        max_size=10,
    )
)
def test_filter_config_questions_round_trip(questions):
    """Test that questions can be round-tripped through filter_config."""
    # Create a data dict from questions
    data = questions.copy()
    
    # Apply filter_config
    config_data, questions_data = filter_config(data)
    
    # Config should be empty for non-underscore keys
    assert len(config_data) == 0
    
    # All questions should be present
    assert len(questions_data) == len(questions)
    
    # Extract defaults from questions_data
    defaults = {}
    for key, value in questions_data.items():
        if isinstance(value, dict) and "default" in value:
            defaults[key] = value["default"]
    
    # Defaults should match original questions  
    assert defaults == questions


# Property 3: verify_copier_version version comparison
@given(
    st.text(min_size=1, max_size=20).filter(
        lambda x: x and not x[0].isdigit() and x != "v"
    )
)
def test_verify_copier_version_invalid_version(invalid_version):
    """Test that verify_copier_version handles invalid version strings."""
    try:
        # Invalid version strings should raise InvalidVersion when parsed
        Version(invalid_version)
        # If it's actually valid, skip this test case
        assume(False)
    except InvalidVersion:
        # Invalid versions should cause an error
        with pytest.raises((InvalidVersion, UnsupportedVersionError)):
            verify_copier_version(invalid_version)


@given(
    st.tuples(
        st.integers(min_value=0, max_value=100),
        st.integers(min_value=0, max_value=100),
        st.integers(min_value=0, max_value=100),
    )
)
def test_verify_copier_version_with_valid_versions(version_tuple):
    """Test verify_copier_version with valid semantic versions."""
    major, minor, patch = version_tuple
    version_str = f"{major}.{minor}.{patch}"
    
    # Mock the copier_version function to control the installed version
    with patch("copier._template.copier_version") as mock_copier_version:
        # Test 1: Exact match should pass
        mock_copier_version.return_value = Version(version_str)
        verify_copier_version(version_str)  # Should not raise
        
        # Test 2: Higher installed version should pass (same major)
        if patch < 100:
            mock_copier_version.return_value = Version(f"{major}.{minor}.{patch + 1}")
            verify_copier_version(version_str)  # Should not raise
        
        # Test 3: Lower installed version should fail
        if patch > 0:
            mock_copier_version.return_value = Version(f"{major}.{minor}.{patch - 1}")
            with pytest.raises(UnsupportedVersionError):
                verify_copier_version(version_str)


# Property 4: Template answers_relpath should never be absolute
@given(
    st.text(min_size=1, max_size=100).filter(
        lambda x: x and not x.startswith("/") and not (len(x) > 1 and x[1] == ":")
    )
)
def test_template_answers_relpath_is_relative(relpath):
    """Test that Template.answers_relpath is always relative."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "template"
        template_dir.mkdir()
        
        # Create a minimal copier.yml
        config_file = template_dir / "copier.yml"
        config_file.write_text(f"_answers_file: {relpath}")
        
        # Create Template instance
        template = Template(url=str(template_dir))
        
        # The answers_relpath should be relative
        assert not template.answers_relpath.is_absolute()
        assert str(template.answers_relpath) == relpath


# Property 5: Template subdirectory is always a string
@given(
    st.one_of(
        st.text(min_size=0, max_size=50),
        st.none(),
    )
)
def test_template_subdirectory_type(subdir_value):
    """Test that Template.subdirectory is always a string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "template"
        template_dir.mkdir()
        
        # Create copier.yml with subdirectory config
        config_file = template_dir / "copier.yml"
        if subdir_value is not None:
            config_file.write_text(f"_subdirectory: {subdir_value}")
        else:
            config_file.write_text("")
        
        # Create Template instance
        template = Template(url=str(template_dir))
        
        # subdirectory should always be a string
        assert isinstance(template.subdirectory, str)
        if subdir_value is not None:
            assert template.subdirectory == str(subdir_value)
        else:
            assert template.subdirectory == ""


# Property 6: Template exclude should always be a tuple
@given(
    st.one_of(
        st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10),
        st.none(),
    )
)
def test_template_exclude_is_tuple(exclude_list):
    """Test that Template.exclude is always a tuple."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "template"
        template_dir.mkdir()
        
        # Create copier.yml with exclude config
        config_file = template_dir / "copier.yml"
        if exclude_list is not None:
            import yaml
            config_file.write_text(yaml.dump({"_exclude": exclude_list}))
        else:
            config_file.write_text("")
        
        # Create Template instance
        template = Template(url=str(template_dir))
        
        # exclude should always be a tuple
        assert isinstance(template.exclude, tuple)
        if exclude_list is not None:
            assert list(template.exclude) == exclude_list