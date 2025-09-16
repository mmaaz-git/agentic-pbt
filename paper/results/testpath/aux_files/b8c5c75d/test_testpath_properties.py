#!/usr/bin/env python3
"""Property-based tests for the testpath module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import os
import tempfile
import stat
import subprocess
from pathlib import Path

from hypothesis import given, strategies as st, assume, settings
import testpath
from testpath import (
    assert_path_exists, assert_not_path_exists,
    assert_isfile, assert_not_isfile,
    assert_isdir, assert_not_isdir,
    assert_islink, assert_not_islink,
    modified_env, temporary_env,
    MockCommand
)


# Strategy for valid environment variable names
env_var_name = st.text(
    alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789',
    min_size=1
).filter(lambda x: not x[0].isdigit())

# Strategy for environment variable values
env_var_value = st.text(min_size=0, max_size=1000).filter(lambda x: '\x00' not in x)


# Property 1: Inverse operations for path assertions
# The code provides pairs like assert_isfile/assert_not_isfile
# For an existing path, exactly one should pass
@given(st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '\x00' not in x))
def test_inverse_assertion_operations_file(filename):
    """Test that assert_isfile and assert_not_isfile are mutually exclusive for files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, filename)
        
        # Create a regular file
        with open(filepath, 'w') as f:
            f.write('test')
        
        # For a regular file, assert_isfile should pass and assert_not_isfile should fail
        assert_isfile(filepath)  # Should pass
        try:
            assert_not_isfile(filepath)  # Should fail
            assert False, "assert_not_isfile should have raised for a regular file"
        except AssertionError as e:
            if "Path is a regular file" not in str(e):
                raise


@given(st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '\x00' not in x))
def test_inverse_assertion_operations_dir(dirname):
    """Test that assert_isdir and assert_not_isdir are mutually exclusive for directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dirpath = os.path.join(tmpdir, dirname)
        os.makedirs(dirpath)
        
        # For a directory, assert_isdir should pass and assert_not_isdir should fail
        assert_isdir(dirpath)  # Should pass
        try:
            assert_not_isdir(dirpath)  # Should fail
            assert False, "assert_not_isdir should have raised for a directory"
        except AssertionError as e:
            if "Path is a directory" not in str(e):
                raise


# Property 2: Environment restoration round-trip
# The docstring explicitly states environment is restored after context exit
@given(
    env_var_name,
    env_var_value,
    env_var_value
)
def test_modified_env_restoration(var_name, original_value, new_value):
    """Test that modified_env restores the environment correctly."""
    assume(original_value != new_value)
    assume(var_name not in ['PATH', 'HOME', 'USER', 'SHELL'])  # Avoid critical vars
    
    # Set initial value
    os.environ[var_name] = original_value
    
    # Modify within context
    with modified_env({var_name: new_value}):
        assert os.environ.get(var_name) == new_value
    
    # Should be restored after context
    assert os.environ.get(var_name) == original_value


@given(
    st.dictionaries(
        env_var_name,
        env_var_value,
        min_size=0,
        max_size=5
    )
)
def test_temporary_env_complete_replacement(new_env):
    """Test that temporary_env completely replaces the environment."""
    # Save critical vars that we need
    critical_vars = {}
    for var in ['PATH', 'HOME', 'USER', 'LD_LIBRARY_PATH', 'PYTHONPATH']:
        if var in os.environ:
            critical_vars[var] = os.environ[var]
    
    # Add critical vars to new_env to avoid breaking the test
    new_env.update(critical_vars)
    
    # Save original environment
    original_env = os.environ.copy()
    
    with temporary_env(new_env):
        # Environment should be exactly what we specified
        current_env = os.environ.copy()
        assert current_env == new_env
    
    # Should be restored after context
    assert os.environ.copy() == original_env


# Property 3: Path string handling consistency
# The _strpath function handles multiple path types
@given(st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '\x00' not in x))
def test_path_type_handling_consistency(filename):
    """Test that assertion functions handle different path types consistently."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath_str = os.path.join(tmpdir, filename)
        filepath_path = Path(filepath_str)
        
        # Create a file
        with open(filepath_str, 'w') as f:
            f.write('test')
        
        # Both string and Path object should work identically
        assert_isfile(filepath_str)
        assert_isfile(filepath_path)
        
        try:
            assert_not_isfile(filepath_str)
            assert False, "Should have raised"
        except AssertionError:
            pass
        
        try:
            assert_not_isfile(filepath_path)
            assert False, "Should have raised"
        except AssertionError:
            pass


# Property 4: MockCommand recording accuracy
# The code explicitly states it records calls to mocked commands
@given(
    st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
    st.lists(
        st.text(min_size=0, max_size=20).filter(lambda x: '\x00' not in x and '\n' not in x),
        min_size=0,
        max_size=5
    )
)
@settings(max_examples=100)
def test_mock_command_recording(cmd_name, args):
    """Test that MockCommand accurately records command calls."""
    assume(cmd_name not in ['python', 'python3', 'bash', 'sh'])  # Avoid real commands
    
    with MockCommand(cmd_name) as mock_cmd:
        # Execute the command with args
        result = subprocess.run(
            [cmd_name] + args,
            capture_output=True,
            text=True,
            shell=False
        )
        
        # Get recorded calls
        calls = mock_cmd.get_calls()
        
        # Should have exactly one call
        assert len(calls) == 1
        
        # The argv should match what we called
        recorded_argv = calls[0]['argv']
        expected_argv = [cmd_name] + args
        assert recorded_argv == expected_argv


# Property 5: Follow symlinks behavior
# The docstrings explicitly describe different behavior based on follow_symlinks
@given(
    st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\x00' not in x),
    st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\x00' not in x)
)
def test_follow_symlinks_behavior(filename, linkname):
    """Test that follow_symlinks parameter works as documented."""
    assume(filename != linkname)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, filename)
        linkpath = os.path.join(tmpdir, linkname)
        
        # Create a regular file
        with open(filepath, 'w') as f:
            f.write('test')
        
        # Create a symlink to the file
        os.symlink(filepath, linkpath)
        
        # With follow_symlinks=True (default), symlink to file should be considered a file
        assert_isfile(linkpath, follow_symlinks=True)
        
        # With follow_symlinks=False, symlink should NOT be considered a file
        try:
            assert_isfile(linkpath, follow_symlinks=False)
            assert False, "Should have raised - symlink is not a regular file"
        except AssertionError as e:
            if "not a regular file" not in str(e):
                raise


# Property 6: Symlink target verification
# assert_islink with 'to' parameter should verify the target
@given(
    st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\x00' not in x),
    st.text(min_size=1, max_size=20).filter(lambda x: '/' not in x and '\x00' not in x)
)
def test_symlink_target_verification(target, linkname):
    """Test that assert_islink correctly verifies symlink targets."""
    assume(target != linkname)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        targetpath = os.path.join(tmpdir, target)
        linkpath = os.path.join(tmpdir, linkname)
        
        # Create target file
        with open(targetpath, 'w') as f:
            f.write('test')
        
        # Create symlink using relative path
        os.symlink(target, linkpath)
        
        # Should pass when checking correct target
        assert_islink(linkpath, to=target)
        
        # Should fail when checking wrong target
        try:
            assert_islink(linkpath, to="wrong_target")
            assert False, "Should have raised for wrong target"
        except AssertionError as e:
            if "Symlink target" not in str(e):
                raise


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])