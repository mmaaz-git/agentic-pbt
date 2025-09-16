#!/usr/bin/env python3
"""Property-based tests for copier.subproject module."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from copier._subproject import Subproject, load_answersfile_data


@given(
    answers=st.dictionaries(
        st.text(min_size=1),
        st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none(),
            st.lists(st.text()),
            st.dictionaries(st.text(), st.text())
        )
    )
)
def test_last_answers_filtering_property(answers):
    """Test that last_answers correctly filters private keys except _src_path and _commit."""
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
        
        # Check filtering property: all keys should either:
        # 1. Not start with underscore, OR
        # 2. Be exactly '_src_path' or '_commit'
        for key in last_answers:
            assert (not key.startswith("_")) or (key in {"_src_path", "_commit"}), \
                f"Key '{key}' should have been filtered out"
        
        # Check that non-private keys are preserved
        for key in answers:
            if not key.startswith("_") or key in {"_src_path", "_commit"}:
                assert key in last_answers, f"Key '{key}' should have been preserved"
                assert last_answers[key] == answers[key], f"Value for '{key}' was modified"


@given(
    answers=st.dictionaries(
        st.text(min_size=1, alphabet=st.characters(blacklist_characters="_")),
        st.text()
    ),
    private_answers=st.dictionaries(
        st.text(min_size=1).map(lambda s: f"_{s}"),
        st.text()
    ),
    src_path=st.one_of(st.none(), st.text(min_size=1)),
    commit=st.one_of(st.none(), st.text(min_size=1))
)
def test_last_answers_special_keys(answers, private_answers, src_path, commit):
    """Test that _src_path and _commit are specially handled in last_answers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = tmpdir_path / ".copier-answers.yml"
        
        # Combine all answers
        all_answers = {}
        all_answers.update(answers)
        all_answers.update(private_answers)
        if src_path is not None:
            all_answers["_src_path"] = src_path
        if commit is not None:
            all_answers["_commit"] = commit
        
        # Write answers to file
        with answers_file.open("w") as f:
            yaml.dump(all_answers, f)
        
        # Create subproject
        subproject = Subproject(local_abspath=tmpdir_path)
        
        # Get last_answers
        last_answers = subproject.last_answers
        
        # Check that regular answers are preserved
        for key, value in answers.items():
            assert key in last_answers
            assert last_answers[key] == value
        
        # Check that private answers are filtered except _src_path and _commit
        for key in private_answers:
            if key not in {"_src_path", "_commit"}:
                assert key not in last_answers, f"Private key '{key}' should be filtered"
        
        # Check that _src_path and _commit are preserved if they existed
        if src_path is not None:
            assert "_src_path" in last_answers
            assert last_answers["_src_path"] == src_path
        if commit is not None:
            assert "_commit" in last_answers
            assert last_answers["_commit"] == commit


@given(is_git_repo=st.booleans())
def test_vcs_property(is_git_repo):
    """Test that vcs property correctly identifies git repos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Mock is_in_git_repo to control the result
        with patch('copier._subproject.is_in_git_repo') as mock_is_in_git_repo:
            mock_is_in_git_repo.return_value = is_git_repo
            
            subproject = Subproject(local_abspath=tmpdir_path)
            vcs = subproject.vcs
            
            # Check property: git repo → "git", non-git → None
            if is_git_repo:
                assert vcs == "git", "Git repo should return 'git'"
            else:
                assert vcs is None, "Non-git repo should return None"
            
            # Verify the function was called with correct path
            mock_is_in_git_repo.assert_called_once_with(tmpdir_path)


@given(
    src_path=st.one_of(st.none(), st.text(min_size=1)),
    commit=st.one_of(st.none(), st.text(min_size=1)),
    other_answers=st.dictionaries(
        st.text(min_size=1).filter(lambda s: s not in {"_src_path", "_commit"}),
        st.text()
    )
)
def test_template_creation_property(src_path, commit, other_answers):
    """Test that template is created when _src_path exists in answers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = tmpdir_path / ".copier-answers.yml"
        
        # Prepare answers
        answers = dict(other_answers)
        if src_path is not None:
            answers["_src_path"] = src_path
        if commit is not None:
            answers["_commit"] = commit
        
        # Write answers to file
        with answers_file.open("w") as f:
            yaml.dump(answers, f)
        
        # Mock Template class to avoid actual template operations
        with patch('copier._subproject.Template') as MockTemplate:
            mock_template_instance = Mock()
            mock_template_instance._cleanup = Mock()
            MockTemplate.return_value = mock_template_instance
            
            subproject = Subproject(local_abspath=tmpdir_path)
            template = subproject.template
            
            # Check property: _src_path exists → template created, else None
            if src_path is not None:
                assert template is not None, "Template should be created when _src_path exists"
                assert template == mock_template_instance
                # Verify Template was called with correct arguments
                MockTemplate.assert_called_once_with(url=src_path, ref=commit)
                # Verify cleanup hook was registered
                assert mock_template_instance._cleanup in subproject._cleanup_hooks
            else:
                assert template is None, "Template should be None when _src_path doesn't exist"
                MockTemplate.assert_not_called()


@given(has_changes=st.booleans())
def test_is_dirty_for_git_repos(has_changes):
    """Test that is_dirty correctly reports git repository status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create mock git command that returns the status output when called
        mock_git_cmd = MagicMock()
        
        # Mock the git status output
        if has_changes:
            # Simulate uncommitted changes
            mock_git_cmd.return_value = " M file.txt\n?? new.txt"
        else:
            # Simulate clean repository  
            mock_git_cmd.return_value = ""
        
        with patch('copier._subproject.get_git') as mock_get_git:
            # get_git() returns a command object that can be called with arguments
            mock_get_git.return_value = mock_git_cmd
            
            # Mock vcs property to return "git"
            with patch.object(Subproject, 'vcs', new_callable=lambda: property(lambda self: "git")):
                subproject = Subproject(local_abspath=tmpdir_path)
                is_dirty = subproject.is_dirty()
                
                # Check property: is_dirty returns True when changes, False when clean
                assert is_dirty == has_changes, \
                    f"is_dirty should return {has_changes} for {'dirty' if has_changes else 'clean'} repo"
                
                # Verify git was called correctly
                mock_git_cmd.assert_called_once_with("status", "--porcelain")


def test_is_dirty_for_non_git_repos():
    """Test that is_dirty returns False for non-git directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Mock vcs property to return None (non-git)
        with patch.object(Subproject, 'vcs', new_callable=lambda: property(lambda self: None)):
            subproject = Subproject(local_abspath=tmpdir_path)
            is_dirty = subproject.is_dirty()
            
            # Check property: non-git repos always return False
            assert is_dirty is False, "is_dirty should return False for non-git directories"


@given(
    file_content=st.one_of(
        st.dictionaries(st.text(), st.text()),
        st.lists(st.text()),
        st.text(),
        st.none()
    ),
    file_exists=st.booleans()
)
def test_load_answersfile_data_property(file_content, file_exists):
    """Test that load_answersfile_data returns dict or handles errors gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = ".copier-answers.yml"
        
        if file_exists:
            # Create the file with content
            file_path = tmpdir_path / answers_file
            with file_path.open("w") as f:
                yaml.dump(file_content, f)
        
        # Load the answers
        result = load_answersfile_data(tmpdir_path, answers_file)
        
        # Check properties
        if file_exists:
            # Should return the content loaded from YAML
            assert result == file_content, "Should return YAML content"
        else:
            # Should return empty dict for missing file
            assert result == {}, "Should return empty dict for missing file"