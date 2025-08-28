#!/usr/bin/env python3
"""Find crash bugs in copier._vcs module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import copier._vcs as vcs


# Test for crashes in get_repo with various string inputs
@given(st.text())
@settings(max_examples=2000)
def test_get_repo_no_crash(url):
    """get_repo should not crash on any string input"""
    try:
        result = vcs.get_repo(url)
        # Should return either a string or None, never crash
        assert result is None or isinstance(result, str)
    except ValueError as e:
        if "embedded null character" in str(e):
            # Found the bug!
            print(f"CRASH BUG: get_repo('{repr(url)}') raises ValueError: {e}")
            raise
        else:
            # Some other ValueError - reraise to investigate
            raise
    except Exception as e:
        # Unexpected exception type
        print(f"UNEXPECTED CRASH: get_repo('{repr(url)}') raises {type(e).__name__}: {e}")
        raise


# Test for crashes in valid_version
@given(st.text())
@settings(max_examples=2000)
def test_valid_version_no_crash(version_str):
    """valid_version should not crash on any string input"""
    try:
        result = vcs.valid_version(version_str)
        # Should return a boolean, never crash
        assert isinstance(result, bool)
    except Exception as e:
        print(f"CRASH BUG: valid_version('{repr(version_str)}') raises {type(e).__name__}: {e}")
        raise


# Test other functions that take string inputs
@given(st.text())
@settings(max_examples=1000)
def test_is_git_repo_root_no_crash(path):
    """is_git_repo_root should not crash on any string input"""
    try:
        result = vcs.is_git_repo_root(path)
        assert isinstance(result, bool)
    except ValueError as e:
        if "embedded null character" in str(e):
            print(f"CRASH BUG: is_git_repo_root('{repr(path)}') raises ValueError: {e}")
            raise
    except Exception as e:
        print(f"UNEXPECTED: is_git_repo_root('{repr(path)}') raises {type(e).__name__}: {e}")
        raise


@given(st.text())
@settings(max_examples=1000)
def test_is_in_git_repo_no_crash(path):
    """is_in_git_repo should not crash on any string input"""
    try:
        result = vcs.is_in_git_repo(path)
        assert isinstance(result, bool)
    except ValueError as e:
        if "embedded null character" in str(e):
            print(f"CRASH BUG: is_in_git_repo('{repr(path)}') raises ValueError: {e}")
            raise
    except Exception as e:
        # OSError is expected for invalid paths
        if not isinstance(e, OSError):
            print(f"UNEXPECTED: is_in_git_repo('{repr(path)}') raises {type(e).__name__}: {e}")
            raise


@given(st.text())
@settings(max_examples=1000)
def test_is_git_shallow_repo_no_crash(path):
    """is_git_shallow_repo should not crash on any string input"""
    try:
        result = vcs.is_git_shallow_repo(path)
        assert isinstance(result, bool)
    except ValueError as e:
        if "embedded null character" in str(e):
            print(f"CRASH BUG: is_git_shallow_repo('{repr(path)}') raises ValueError: {e}")
            raise
    except Exception as e:
        # OSError is expected for invalid paths
        if not isinstance(e, OSError):
            print(f"UNEXPECTED: is_git_shallow_repo('{repr(path)}') raises {type(e).__name__}: {e}")
            raise


if __name__ == "__main__":
    print("Testing for crash bugs...")
    
    # Test each function
    try:
        test_get_repo_no_crash()
        print("✓ get_repo: No crashes found")
    except Exception as e:
        print(f"✗ get_repo: Found crash")
    
    try:
        test_valid_version_no_crash()
        print("✓ valid_version: No crashes found")
    except Exception as e:
        print(f"✗ valid_version: Found crash")
    
    try:
        test_is_git_repo_root_no_crash()
        print("✓ is_git_repo_root: No crashes found") 
    except Exception as e:
        print(f"✗ is_git_repo_root: Found crash")
    
    try:
        test_is_in_git_repo_no_crash()
        print("✓ is_in_git_repo: No crashes found")
    except Exception as e:
        print(f"✗ is_in_git_repo: Found crash")
    
    try:
        test_is_git_shallow_repo_no_crash()
        print("✓ is_git_shallow_repo: No crashes found")
    except Exception as e:
        print(f"✗ is_git_shallow_repo: Found crash")