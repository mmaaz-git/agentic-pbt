#!/usr/bin/env python3
"""Property-based tests for testpath.tempdir module using Hypothesis."""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import testpath.tempdir
from hypothesis import given, strategies as st, settings, assume
import string


# Strategy for valid filenames (avoiding path separators and null bytes)
valid_filename_chars = string.ascii_letters + string.digits + "_-.() "
filename_strategy = st.text(
    alphabet=valid_filename_chars, 
    min_size=1, 
    max_size=100
).filter(lambda x: x.strip() and not x.startswith('.'))

# Strategy for file modes
mode_strategy = st.sampled_from(['r', 'w', 'a', 'r+', 'w+', 'a+', 
                                  'rb', 'wb', 'ab', 'r+b', 'w+b', 'a+b'])


@given(filename=filename_strategy)
@settings(max_examples=100)
def test_named_file_in_temp_dir_creates_file(filename):
    """Test that NamedFileInTemporaryDirectory creates a file with the given name."""
    with testpath.tempdir.NamedFileInTemporaryDirectory(filename, mode='w') as f:
        # File should exist
        assert os.path.exists(f.name), f"File {f.name} does not exist"
        
        # File should have the correct name
        assert os.path.basename(f.name) == filename, f"Filename mismatch: expected {filename}, got {os.path.basename(f.name)}"
        
        # File should be in a temporary directory
        parent_dir = os.path.dirname(f.name)
        temp_dir = tempfile.gettempdir()
        assert parent_dir.startswith(temp_dir), f"File not in temp directory: {parent_dir}"
        
        # Should be able to write to the file
        f.write("test content")
        f.flush()
        
        # File should still exist after flush
        assert os.path.exists(f.name), "File disappeared after flush"


@given(filename=filename_strategy, mode=mode_strategy)
def test_named_file_mode_handling(filename, mode):
    """Test that NamedFileInTemporaryDirectory respects the mode parameter."""
    # Skip read-only modes for this test since we need to create the file first
    if mode.startswith('r') and '+' not in mode:
        assume(False)
    
    try:
        with testpath.tempdir.NamedFileInTemporaryDirectory(filename, mode=mode) as f:
            # Check that file is opened
            assert not f.closed, "File should be open"
            
            # Check mode is correct (handle binary modes)
            actual_mode = f.mode
            # Python may normalize modes (e.g., 'w+b' -> 'wb+')
            if 'b' in mode:
                assert 'b' in actual_mode, f"Binary mode not preserved: expected {mode}, got {actual_mode}"
            
            # Try basic operations based on mode
            if 'w' in mode or 'a' in mode or '+' in mode:
                if 'b' in mode:
                    f.write(b"test")
                else:
                    f.write("test")
                f.flush()
    except (OSError, ValueError) as e:
        # Some mode combinations might not be supported
        assume(False)


@given(filenames=st.lists(filename_strategy, min_size=2, max_size=5, unique=True))
def test_multiple_named_files_no_conflict(filenames):
    """Test that multiple NamedFileInTemporaryDirectory instances don't conflict."""
    contexts = []
    files = []
    
    try:
        # Create multiple files
        for filename in filenames:
            ctx = testpath.tempdir.NamedFileInTemporaryDirectory(filename, mode='w')
            f = ctx.__enter__()
            contexts.append(ctx)
            files.append(f)
            
            # Write unique content
            f.write(f"Content for {filename}")
            f.flush()
        
        # All files should exist and have different paths
        paths = [f.name for f in files]
        assert len(set(paths)) == len(paths), "Files have conflicting paths"
        
        for f, filename in zip(files, filenames):
            assert os.path.exists(f.name), f"File {f.name} does not exist"
            assert os.path.basename(f.name) == filename
            
    finally:
        # Cleanup
        for ctx in contexts:
            try:
                ctx.__exit__(None, None, None)
            except:
                pass


def test_temp_working_directory_changes_cwd():
    """Test that TemporaryWorkingDirectory changes the current working directory."""
    original_cwd = os.getcwd()
    
    with testpath.tempdir.TemporaryWorkingDirectory() as tmpdir:
        current_cwd = os.getcwd()
        
        # CWD should have changed
        assert current_cwd != original_cwd, "Working directory did not change"
        
        # CWD should be the temp directory
        assert current_cwd == tmpdir, f"CWD mismatch: expected {tmpdir}, got {current_cwd}"
        
        # Should be in a temporary location
        assert current_cwd.startswith(tempfile.gettempdir()), "Not in temp directory"
    
    # CWD should be restored
    assert os.getcwd() == original_cwd, "Working directory not restored"


def test_temp_working_directory_nested():
    """Test that nested TemporaryWorkingDirectory contexts work correctly."""
    original_cwd = os.getcwd()
    
    with testpath.tempdir.TemporaryWorkingDirectory() as tmpdir1:
        cwd1 = os.getcwd()
        assert cwd1 == tmpdir1
        assert cwd1 != original_cwd
        
        with testpath.tempdir.TemporaryWorkingDirectory() as tmpdir2:
            cwd2 = os.getcwd()
            assert cwd2 == tmpdir2
            assert cwd2 != cwd1
            assert cwd2 != original_cwd
        
        # Should be back to first temp directory
        assert os.getcwd() == cwd1, "Did not restore to first temp directory"
    
    # Should be back to original
    assert os.getcwd() == original_cwd, "Did not restore to original directory"


@given(filename=filename_strategy)
def test_named_file_cleanup_on_exception(filename):
    """Test that NamedFileInTemporaryDirectory cleans up even when exception occurs."""
    file_path = None
    dir_path = None
    
    try:
        with testpath.tempdir.NamedFileInTemporaryDirectory(filename, mode='w') as f:
            file_path = f.name
            dir_path = os.path.dirname(f.name)
            assert os.path.exists(file_path)
            assert os.path.exists(dir_path)
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # After exception, the temp directory should be cleaned up
    assert not os.path.exists(file_path), "File not cleaned up after exception"
    assert not os.path.exists(dir_path), "Directory not cleaned up after exception"


def test_temp_working_directory_cleanup_on_exception():
    """Test that TemporaryWorkingDirectory restores CWD even when exception occurs."""
    original_cwd = os.getcwd()
    temp_dir_path = None
    
    try:
        with testpath.tempdir.TemporaryWorkingDirectory() as tmpdir:
            temp_dir_path = tmpdir
            assert os.getcwd() == tmpdir
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # CWD should be restored even after exception
    assert os.getcwd() == original_cwd, "CWD not restored after exception"
    
    # Temp directory should be cleaned up
    assert not os.path.exists(temp_dir_path), "Temp directory not cleaned up"


@given(filename=filename_strategy)
def test_named_file_reopen_capability(filename):
    """Test that files created can be reopened (main purpose of this class)."""
    with testpath.tempdir.NamedFileInTemporaryDirectory(filename, mode='w') as f:
        test_content = "Test content for reopen"
        f.write(test_content)
        f.close()  # Close the file handle
        
        # File should still exist after closing
        assert os.path.exists(f.name), "File disappeared after close"
        
        # Should be able to reopen the file
        with open(f.name, 'r') as f2:
            content = f2.read()
            assert content == test_content, f"Content mismatch: expected '{test_content}', got '{content}'"
    
    # After context exit, file should be gone
    assert not os.path.exists(f.name), "File not cleaned up after context exit"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])