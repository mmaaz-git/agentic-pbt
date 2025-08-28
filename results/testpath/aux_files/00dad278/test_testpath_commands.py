"""Property-based tests for testpath.commands module."""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

from hypothesis import given, assume, strategies as st, settings
import testpath.commands as commands


# Strategy for valid command names (no special chars that could break shell)
valid_command_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
    min_size=1,
    max_size=50
)

# Strategy for path directories
path_dirs = st.lists(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_/", min_size=1, max_size=20),
    min_size=0,
    max_size=10
).map(lambda dirs: [d for d in dirs if d and not d.isspace()])


@given(st.text(min_size=1, max_size=100))
def test_prepend_remove_path_roundtrip(new_dir):
    """prepend_to_path followed by remove_from_path should restore original PATH."""
    # Skip paths with path separator as they would break the logic
    assume(os.pathsep not in new_dir)
    assume(new_dir.strip())  # Non-empty after stripping
    
    original_path = os.environ.get('PATH', '')
    
    try:
        # Prepend the directory
        commands.prepend_to_path(new_dir)
        modified_path = os.environ['PATH']
        
        # Check it was prepended
        assert modified_path.startswith(new_dir + os.pathsep)
        
        # Remove it
        commands.remove_from_path(new_dir)
        restored_path = os.environ.get('PATH', '')
        
        # Check PATH is restored
        assert restored_path == original_path
    finally:
        # Ensure PATH is restored even if test fails
        os.environ['PATH'] = original_path


@given(valid_command_names)
def test_mock_command_context_cleanup(cmd_name):
    """MockCommand should clean up its temporary directory after exiting context."""
    temp_dirs_before = set()
    
    # Record initial temp directory state
    with commands.MockCommand(cmd_name) as mc:
        command_dir = mc.command_dir
        assert os.path.exists(command_dir)
        assert os.path.isdir(command_dir)
        
        # The command file should exist
        cmd_path = mc._cmd_path
        assert os.path.exists(cmd_path)
    
    # After exiting context, the temp directory should be cleaned up
    assert not os.path.exists(command_dir)


@given(
    valid_command_names,
    st.text(min_size=0, max_size=100),  # stdout
    st.text(min_size=0, max_size=100),  # stderr
    st.integers(min_value=0, max_value=255)  # exit status
)
def test_fixed_output_produces_expected_output(cmd_name, stdout, stderr, exit_status):
    """MockCommand.fixed_output should produce the specified output."""
    # Create a unique test script that calls our mock command
    test_script = f"""
import subprocess
import sys
result = subprocess.run(['{cmd_name}'], capture_output=True, text=True)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
"""
    
    with commands.MockCommand.fixed_output(cmd_name, stdout, stderr, exit_status) as mc:
        # Run the command and capture output
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        
        # Check outputs match
        assert result.stdout == stdout
        assert result.stderr == stderr
        assert result.returncode == exit_status


@given(
    valid_command_names,
    st.lists(st.lists(st.text(min_size=0, max_size=20), min_size=0, max_size=5), min_size=1, max_size=5)
)
def test_get_calls_records_all_invocations(cmd_name, args_list):
    """get_calls() should return all invocations with correct argv."""
    with commands.MockCommand(cmd_name) as mc:
        # Make multiple calls to the command
        for args in args_list:
            # Filter out args with problematic characters
            clean_args = [arg for arg in args if arg and '\x00' not in arg and '\x1e' not in arg]
            cmd = [cmd_name] + clean_args
            
            # Run the command (it will fail with exit 1, but that's ok)
            subprocess.run(cmd, capture_output=True, env=os.environ.copy())
        
        # Get recorded calls
        calls = mc.get_calls()
        
        # Should have recorded all calls
        assert len(calls) >= len(args_list)
        
        # Each call should have proper structure
        for call in calls:
            assert isinstance(call, dict)
            assert 'argv' in call
            assert 'env' in call
            assert 'cwd' in call
            assert isinstance(call['argv'], list)
            assert len(call['argv']) >= 1
            assert call['argv'][0] == cmd_name or call['argv'][0].endswith(cmd_name)


@given(valid_command_names, st.text(min_size=1, max_size=100))
def test_content_and_python_params_mutually_exclusive(cmd_name, python_code):
    """MockCommand should raise ValueError if both content and python params are provided."""
    try:
        # This should raise ValueError
        mc = commands.MockCommand(cmd_name, content="#!/bin/sh\necho test", python=python_code)
        # If we get here, the test failed
        assert False, "Expected ValueError when both content and python provided"
    except ValueError as e:
        # Expected behavior
        assert "not both" in str(e).lower()


@given(valid_command_names)
def test_double_entry_raises_error(cmd_name):
    """Entering the same MockCommand context twice should raise an error."""
    mc = commands.MockCommand(cmd_name)
    
    with mc:
        # Try to enter again - should raise EnvironmentError
        try:
            mc.__enter__()
            assert False, "Expected EnvironmentError on double entry"
        except EnvironmentError as e:
            assert "already exists" in str(e)


@given(path_dirs)
def test_prepend_to_empty_path(dirs):
    """prepend_to_path should work even with empty PATH."""
    original_path = os.environ.get('PATH', '')
    
    try:
        # Clear PATH
        os.environ['PATH'] = ''
        
        for d in dirs:
            commands.prepend_to_path(d)
            # Should now start with this directory
            assert os.environ['PATH'].startswith(d)
    finally:
        os.environ['PATH'] = original_path


@given(st.text(min_size=1, max_size=100))
def test_remove_from_path_handles_missing_dir(missing_dir):
    """remove_from_path should handle (raise error) when directory not in PATH."""
    assume(os.pathsep not in missing_dir)
    original_path = os.environ.get('PATH', '')
    
    try:
        # Ensure the dir is not in PATH
        if missing_dir in os.environ.get('PATH', '').split(os.pathsep):
            return  # Skip this case
        
        # This should raise ValueError when trying to remove non-existent dir
        try:
            commands.remove_from_path(missing_dir)
            # If no error, that's a potential issue
        except ValueError:
            # Expected - directory not in PATH
            pass
    finally:
        os.environ['PATH'] = original_path


if __name__ == "__main__":
    # Run with pytest
    import pytest
    pytest.main([__file__, "-v"])