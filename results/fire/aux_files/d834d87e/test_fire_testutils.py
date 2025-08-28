import os
import tempfile
from pathlib import Path

from hypothesis import given, strategies as st, assume
from fire.testutils import ChangeDirectory


# Strategy for valid directory paths
def valid_directory_paths():
    """Generate valid directory paths that exist."""
    # Use existing directories we know about
    dirs = [
        os.getcwd(),
        '/',
        '/tmp',
        '/root',
        tempfile.gettempdir(),
    ]
    # Add parent directories
    current = os.getcwd()
    while current != '/':
        dirs.append(current)
        current = os.path.dirname(current)
    
    return st.sampled_from(dirs)


@given(valid_directory_paths())
def test_change_directory_round_trip(directory):
    """Test that ChangeDirectory restores original directory after context."""
    original_dir = os.getcwd()
    
    with ChangeDirectory(directory):
        # We're now in a different directory
        pass
    
    # Should be back to original directory
    assert os.getcwd() == original_dir, f"Directory not restored: expected {original_dir}, got {os.getcwd()}"


@given(valid_directory_paths())
def test_change_directory_invariant_during_context(directory):
    """Test that current directory is correct during the context."""
    original_dir = os.getcwd()
    
    with ChangeDirectory(directory):
        # Should be in the requested directory
        current = os.getcwd()
        # Normalize paths to handle symlinks and relative paths
        assert os.path.realpath(current) == os.path.realpath(directory), \
            f"Not in expected directory during context: expected {directory}, got {current}"
    
    # Verify we're back
    assert os.getcwd() == original_dir


@given(valid_directory_paths())
def test_change_directory_yields_directory(directory):
    """Test that ChangeDirectory yields the directory it changes to."""
    with ChangeDirectory(directory) as yielded_dir:
        assert yielded_dir == directory, f"Yielded wrong directory: expected {directory}, got {yielded_dir}"


@given(st.text(min_size=1))
def test_change_directory_with_invalid_path(path):
    """Test ChangeDirectory behavior with invalid paths."""
    # Skip if the path accidentally exists
    assume(not os.path.exists(path))
    
    original_dir = os.getcwd()
    
    # Should raise an exception for invalid directory
    try:
        with ChangeDirectory(path):
            pass
        # If we get here without exception, that's unexpected
        assert False, f"ChangeDirectory accepted invalid path: {path}"
    except (FileNotFoundError, OSError, NotADirectoryError, ValueError):
        # Expected exceptions - ValueError for null chars
        pass
    
    # Even after exception, should be in original directory
    assert os.getcwd() == original_dir, \
        f"Directory not restored after exception: expected {original_dir}, got {os.getcwd()}"


@given(valid_directory_paths(), valid_directory_paths())
def test_nested_change_directory(dir1, dir2):
    """Test nested ChangeDirectory contexts."""
    original_dir = os.getcwd()
    
    with ChangeDirectory(dir1):
        assert os.path.realpath(os.getcwd()) == os.path.realpath(dir1)
        
        with ChangeDirectory(dir2):
            assert os.path.realpath(os.getcwd()) == os.path.realpath(dir2)
        
        # Should be back to dir1
        assert os.path.realpath(os.getcwd()) == os.path.realpath(dir1)
    
    # Should be back to original
    assert os.getcwd() == original_dir


def test_change_directory_with_file_path():
    """Test that ChangeDirectory fails appropriately with file paths."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        file_path = f.name
    
    original_dir = os.getcwd()
    
    try:
        with ChangeDirectory(file_path):
            pass
        assert False, "ChangeDirectory accepted a file path instead of directory"
    except (NotADirectoryError, OSError):
        # Expected
        pass
    finally:
        # Cleanup
        os.unlink(file_path)
    
    # Should still be in original directory
    assert os.getcwd() == original_dir


@given(st.integers(min_value=1, max_value=10))
def test_multiple_sequential_changes(num_changes):
    """Test multiple sequential directory changes."""
    original_dir = os.getcwd()
    dirs = [tempfile.gettempdir(), '/', '/root', os.getcwd()]
    
    for i in range(num_changes):
        chosen_dir = dirs[i % len(dirs)]
        with ChangeDirectory(chosen_dir):
            assert os.path.realpath(os.getcwd()) == os.path.realpath(chosen_dir)
    
    # Should always return to original
    assert os.getcwd() == original_dir