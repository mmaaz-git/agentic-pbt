#!/usr/bin/env python3
"""Property-based tests for testpath.asserts module."""

import os
import stat
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, strategies as st

import testpath.asserts as asserts


# Strategy for generating safe file paths (avoiding system paths)
@st.composite
def temp_paths(draw):
    """Generate temporary file paths that are safe to create/delete."""
    base = tempfile.gettempdir()
    name = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_', min_size=1, max_size=20))
    return os.path.join(base, f"test_{name}")


@st.composite
def existing_paths(draw):
    """Generate paths to existing filesystem entries."""
    path_type = draw(st.sampled_from(['file', 'dir', 'symlink', 'broken_symlink']))
    base = tempfile.gettempdir()
    name = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_', min_size=1, max_size=15))
    path = os.path.join(base, f"hypo_test_{name}")
    
    # Clean up any existing path first
    try:
        if os.path.islink(path) or os.path.exists(path):
            if os.path.isdir(path) and not os.path.islink(path):
                os.rmdir(path)
            else:
                os.remove(path)
    except:
        pass
    
    if path_type == 'file':
        with open(path, 'w') as f:
            f.write('test')
    elif path_type == 'dir':
        os.makedirs(path, exist_ok=True)
    elif path_type == 'symlink':
        target = os.path.join(base, f"hypo_target_{name}")
        with open(target, 'w') as f:
            f.write('target')
        os.symlink(target, path)
    elif path_type == 'broken_symlink':
        target = os.path.join(base, f"hypo_nonexist_{name}")
        os.symlink(target, path)
    
    return path, path_type


# Property 1: Inverse operations - assert_path_exists and assert_not_path_exists
@given(existing_paths())
def test_exists_inverse_property(path_info):
    """Test that assert_path_exists and assert_not_path_exists are inverses."""
    path, path_type = path_info
    
    # If path exists, assert_path_exists should pass and assert_not_path_exists should fail
    if os.path.exists(path):
        asserts.assert_path_exists(path)  # Should not raise
        with pytest.raises(AssertionError):
            asserts.assert_not_path_exists(path)
    else:
        # For broken symlinks, exists() returns False but lstat succeeds
        if path_type == 'broken_symlink':
            # broken symlinks "exist" in the sense that lstat works
            asserts.assert_path_exists(path)  # Should not raise  
            with pytest.raises(AssertionError):
                asserts.assert_not_path_exists(path)
        else:
            with pytest.raises(AssertionError):
                asserts.assert_path_exists(path)
            asserts.assert_not_path_exists(path)  # Should not raise
    
    # Cleanup
    try:
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        elif os.path.exists(path):
            os.remove(path)
    except:
        pass


# Property 2: File type mutual exclusivity
@given(existing_paths())
def test_file_type_exclusivity(path_info):
    """Test that a path can only be one type at a time."""
    path, path_type = path_info
    
    type_checks = [
        (asserts.assert_isfile, stat.S_ISREG),
        (asserts.assert_isdir, stat.S_ISDIR),
        (asserts.assert_islink, stat.S_ISLNK),
    ]
    
    # Count how many type assertions pass
    passing_types = []
    for assert_func, stat_check in type_checks:
        try:
            if assert_func == asserts.assert_islink:
                # islink checks with follow_symlinks=False
                assert_func(path)
            else:
                # Others check with follow_symlinks=True by default
                assert_func(path, follow_symlinks=True)
            passing_types.append(assert_func.__name__)
        except AssertionError:
            pass
    
    # With follow_symlinks=True, symlinks to files/dirs will match their target type
    # So we might have multiple passing types in that case
    if path_type == 'symlink':
        # A symlink can appear as both a link AND its target type
        assert len(passing_types) <= 2, f"Path {path} matched types: {passing_types}"
    elif path_type == 'broken_symlink':
        # Broken symlinks should only match islink
        assert passing_types == ['assert_islink'], f"Broken symlink matched: {passing_types}"
    else:
        # Regular files and dirs should match exactly one type
        assert len(passing_types) == 1, f"Path {path} matched {len(passing_types)} types: {passing_types}"
    
    # Cleanup
    try:
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        elif os.path.exists(path):
            os.remove(path)
    except:
        pass


# Property 3: Not-X functions have inverse behavior
@given(existing_paths())
def test_not_functions_inverse(path_info):
    """Test that assert_not_isX functions are inverses of assert_isX."""
    path, path_type = path_info
    
    pairs = [
        (asserts.assert_isfile, asserts.assert_not_isfile),
        (asserts.assert_isdir, asserts.assert_not_isdir),
        (asserts.assert_islink, asserts.assert_not_islink),
    ]
    
    for positive, negative in pairs:
        # Special handling for islink which uses follow_symlinks=False
        if positive == asserts.assert_islink:
            try:
                positive(path)
                # If positive passes, negative should fail
                with pytest.raises(AssertionError):
                    negative(path)
            except AssertionError:
                # If positive fails, negative should pass
                negative(path)
        else:
            # For file and dir checks with follow_symlinks=True
            try:
                positive(path, follow_symlinks=True)
                # If positive passes, negative should fail
                with pytest.raises(AssertionError):
                    negative(path, follow_symlinks=True)
            except AssertionError:
                # If positive fails, negative should pass
                negative(path, follow_symlinks=True)
    
    # Cleanup
    try:
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        elif os.path.exists(path):
            os.remove(path)
    except:
        pass


# Property 4: Custom error messages are preserved
@given(
    existing_paths(),
    st.text(min_size=1, max_size=100)
)
def test_custom_message_preservation(path_info, custom_msg):
    """Test that custom error messages are preserved exactly."""
    path, path_type = path_info
    
    # Test with assert_path_exists on non-existent path
    non_existent = path + "_nonexistent_xyzabc"
    try:
        asserts.assert_path_exists(non_existent, msg=custom_msg)
        assert False, "Should have raised AssertionError"
    except AssertionError as e:
        assert str(e) == custom_msg, f"Expected message '{custom_msg}', got '{str(e)}'"
    
    # Test with assert_not_path_exists on existing path  
    if os.path.exists(path):
        try:
            asserts.assert_not_path_exists(path, msg=custom_msg)
            assert False, "Should have raised AssertionError"
        except AssertionError as e:
            assert str(e) == custom_msg, f"Expected message '{custom_msg}', got '{str(e)}'"
    
    # Cleanup
    try:
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)
        elif os.path.exists(path):
            os.remove(path)
    except:
        pass


# Property 5: Symlink follow behavior changes results
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_', min_size=1, max_size=15))
def test_symlink_follow_behavior(name):
    """Test that follow_symlinks parameter changes behavior for symlinks."""
    base = tempfile.gettempdir()
    target_file = os.path.join(base, f"hypo_target_{name}")
    symlink_path = os.path.join(base, f"hypo_symlink_{name}")
    
    # Cleanup first
    for p in [symlink_path, target_file]:
        try:
            if os.path.islink(p) or os.path.exists(p):
                os.remove(p)
        except:
            pass
    
    # Create a file and a symlink to it
    with open(target_file, 'w') as f:
        f.write('content')
    os.symlink(target_file, symlink_path)
    
    # With follow_symlinks=True, symlink should be treated as a file
    asserts.assert_isfile(symlink_path, follow_symlinks=True)
    with pytest.raises(AssertionError):
        asserts.assert_islink(symlink_path)  # islink always uses follow_symlinks=False
    
    # With follow_symlinks=False, symlink should NOT be treated as a file
    with pytest.raises(AssertionError):
        asserts.assert_isfile(symlink_path, follow_symlinks=False)
    
    # islink should always detect it as a symlink
    asserts.assert_islink(symlink_path)
    
    # Cleanup
    os.remove(symlink_path)
    os.remove(target_file)


# Property 6: Path normalization consistency
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_', min_size=1, max_size=15))
def test_path_type_handling(name):
    """Test that different path representations are handled consistently."""
    base = tempfile.gettempdir()
    test_file = os.path.join(base, f"hypo_pathtest_{name}")
    
    # Cleanup first
    try:
        if os.path.exists(test_file):
            os.remove(test_file)
    except:
        pass
    
    # Create a test file
    with open(test_file, 'w') as f:
        f.write('test')
    
    # Test with string path
    asserts.assert_isfile(test_file)
    
    # Test with Path object
    path_obj = Path(test_file)
    asserts.assert_isfile(path_obj)
    
    # Both should behave identically
    asserts.assert_path_exists(test_file)
    asserts.assert_path_exists(path_obj)
    
    # Cleanup
    os.remove(test_file)