#!/usr/bin/env python3
"""Additional edge case tests for copier.subproject module."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from copier._subproject import Subproject, load_answersfile_data


@given(
    answers=st.dictionaries(
        st.one_of(
            st.text(min_size=1),
            st.text(min_size=0).map(lambda s: f"_{s}"),  # Private keys
            st.just("_src_path"),
            st.just("_commit")
        ),
        st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none(),
            st.lists(st.text()),
            st.dictionaries(st.text(), st.text()),
            st.recursive(
                st.one_of(st.text(), st.integers(), st.booleans()),
                lambda children: st.dictionaries(st.text(), children, max_size=3),
                max_leaves=10
            )
        ),
        min_size=0,
        max_size=50
    )
)
@settings(max_examples=1000)
def test_last_answers_complex_data_structures(answers):
    """Test last_answers with complex nested data structures and edge cases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = tmpdir_path / ".copier-answers.yml"
        
        # Write answers to file
        with answers_file.open("w") as f:
            yaml.dump(answers, f)
        
        # Create subproject
        subproject = Subproject(local_abspath=tmpdir_path)
        
        # Get last_answers
        last_answers = subproject.last_answers
        
        # Check filtering property
        for key in last_answers:
            assert (not key.startswith("_")) or (key in {"_src_path", "_commit"}), \
                f"Key '{key}' should have been filtered out"
        
        # Check preservation of values (including nested structures)
        for key, value in answers.items():
            if not key.startswith("_") or key in {"_src_path", "_commit"}:
                assert key in last_answers, f"Key '{key}' should have been preserved"
                assert last_answers[key] == value, f"Value for '{key}' was modified"


@given(
    answers_file_name=st.text(min_size=1).filter(lambda s: "/" not in s and "\\" not in s),
    answers=st.dictionaries(
        st.text(min_size=1),
        st.text()
    )
)
def test_custom_answers_file_path(answers_file_name, answers):
    """Test Subproject with custom answers file paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = tmpdir_path / answers_file_name
        
        # Write answers to custom file
        with answers_file.open("w") as f:
            yaml.dump(answers, f)
        
        # Create subproject with custom answers file
        subproject = Subproject(
            local_abspath=tmpdir_path,
            answers_relpath=Path(answers_file_name)
        )
        
        # Get last_answers
        last_answers = subproject.last_answers
        
        # Should load from custom file
        for key, value in answers.items():
            if not key.startswith("_") or key in {"_src_path", "_commit"}:
                assert key in last_answers, f"Key '{key}' should have been loaded"
                assert last_answers[key] == value


@given(
    yaml_content=st.text()
)
def test_load_answersfile_invalid_yaml(yaml_content):
    """Test load_answersfile_data with potentially invalid YAML content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = ".copier-answers.yml"
        file_path = tmpdir_path / answers_file
        
        # Write potentially invalid YAML
        with file_path.open("w") as f:
            f.write(yaml_content)
        
        try:
            result = load_answersfile_data(tmpdir_path, answers_file)
            # If it succeeded, result should be dict-like or None
            assert isinstance(result, (dict, type(None))), \
                f"Unexpected result type: {type(result)}"
        except yaml.YAMLError:
            # YAML parsing errors are acceptable for invalid content
            pass


@given(
    dir_structure=st.lists(
        st.text(min_size=1, max_size=20).filter(lambda s: "/" not in s and "\\" not in s),
        min_size=0,
        max_size=10
    )
)
def test_answers_file_is_directory(dir_structure):
    """Test behavior when answers file path points to a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create nested directory structure
        current_path = tmpdir_path / ".copier-answers.yml"
        current_path.mkdir(parents=True, exist_ok=True)
        
        for dirname in dir_structure:
            (current_path / dirname).mkdir(exist_ok=True)
        
        # Should return empty dict when path is a directory
        result = load_answersfile_data(tmpdir_path, ".copier-answers.yml")
        assert result == {}, "Should return empty dict when answers file is a directory"
        
        # Subproject should handle this gracefully
        subproject = Subproject(local_abspath=tmpdir_path)
        last_answers = subproject.last_answers
        assert last_answers == {}, "Should return empty dict when answers file is a directory"


@given(
    symlink_target=st.text(min_size=1).filter(lambda s: "/" not in s),
    create_target=st.booleans(),
    target_content=st.dictionaries(st.text(), st.text())
)
def test_answers_file_symlink(symlink_target, create_target, target_content):
    """Test behavior with symlinked answers files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = tmpdir_path / ".copier-answers.yml"
        target_file = tmpdir_path / symlink_target
        
        if create_target:
            # Create target file
            with target_file.open("w") as f:
                yaml.dump(target_content, f)
        
        # Create symlink
        try:
            answers_file.symlink_to(target_file)
        except (OSError, FileExistsError):
            # Skip if symlinks not supported
            return
        
        # Load through symlink
        result = load_answersfile_data(tmpdir_path, ".copier-answers.yml")
        
        if create_target:
            assert result == target_content, "Should load content through symlink"
        else:
            assert result == {}, "Should return empty dict for broken symlink"


@given(
    has_cleanup_hooks=st.booleans(),
    num_hooks=st.integers(min_value=0, max_value=10)
)
def test_cleanup_hooks_execution(has_cleanup_hooks, num_hooks):
    """Test that cleanup hooks are properly managed and executed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        subproject = Subproject(local_abspath=tmpdir_path)
        
        # Track which hooks were called
        called_hooks = []
        
        if has_cleanup_hooks:
            # Add mock cleanup hooks
            for i in range(num_hooks):
                hook = Mock(side_effect=lambda i=i: called_hooks.append(i))
                subproject._cleanup_hooks.append(hook)
        
        # Execute cleanup
        subproject._cleanup()
        
        # Verify all hooks were called
        if has_cleanup_hooks:
            assert len(called_hooks) == num_hooks, "All cleanup hooks should be called"
            # Verify they were called in order
            assert called_hooks == list(range(num_hooks)), "Hooks should be called in order"


@given(
    answers=st.dictionaries(
        st.text(min_size=1),
        st.text(),
        min_size=100,  # Large dictionary
        max_size=1000
    )
)
@settings(max_examples=10)
def test_large_answers_file(answers):
    """Test handling of large answers files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = tmpdir_path / ".copier-answers.yml"
        
        # Add special keys
        answers["_src_path"] = "https://example.com/template"
        answers["_commit"] = "abc123"
        answers["_private_key"] = "should_be_filtered"
        
        # Write large answers file
        with answers_file.open("w") as f:
            yaml.dump(answers, f)
        
        # Create subproject
        subproject = Subproject(local_abspath=tmpdir_path)
        
        # Get last_answers
        last_answers = subproject.last_answers
        
        # Check that private keys are filtered correctly even in large files
        assert "_private_key" not in last_answers
        assert "_src_path" in last_answers
        assert "_commit" in last_answers
        
        # Check that public keys are preserved
        public_keys = [k for k in answers.keys() if not k.startswith("_")]
        for key in public_keys:
            assert key in last_answers