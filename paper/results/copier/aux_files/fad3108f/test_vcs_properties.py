#!/usr/bin/env python3
"""Property-based tests for copier._vcs module"""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from packaging import version
from packaging.version import InvalidVersion
import copier._vcs as vcs


# Test 1: get_repo idempotence property
@given(st.text(min_size=1))
@settings(max_examples=1000)
def test_get_repo_idempotence(url):
    """get_repo should be idempotent: get_repo(get_repo(x)) == get_repo(x)"""
    first_result = vcs.get_repo(url)
    if first_result is not None:
        second_result = vcs.get_repo(first_result)
        assert second_result == first_result, \
            f"get_repo is not idempotent: get_repo('{url}') = '{first_result}', " \
            f"but get_repo('{first_result}') = '{second_result}'"


# Test 2: gh: prefix transformation
@given(st.text(min_size=1).filter(lambda x: not x.startswith('/')))
@settings(max_examples=500)
def test_get_repo_gh_prefix(path):
    """URLs starting with gh: should transform to https://github.com/"""
    assume(not any(c in path for c in ['\n', '\r', '\0']))
    
    # Test without .git extension
    url = f"gh:{path}"
    result = vcs.get_repo(url)
    
    if path.endswith('.git'):
        expected = f"https://github.com/{path}"
    else:
        expected = f"https://github.com/{path}.git"
    
    assert result == expected, \
        f"get_repo('gh:{path}') = '{result}', expected '{expected}'"


# Test 3: gl: prefix transformation  
@given(st.text(min_size=1).filter(lambda x: not x.startswith('/')))
@settings(max_examples=500)
def test_get_repo_gl_prefix(path):
    """URLs starting with gl: should transform to https://gitlab.com/"""
    assume(not any(c in path for c in ['\n', '\r', '\0']))
    
    url = f"gl:{path}"
    result = vcs.get_repo(url)
    
    if path.endswith('.git'):
        expected = f"https://gitlab.com/{path}"
    else:
        expected = f"https://gitlab.com/{path}.git"
    
    assert result == expected, \
        f"get_repo('gl:{path}') = '{result}', expected '{expected}'"


# Test 4: valid_version should correctly identify PEP 440 versions
@given(st.text())
@settings(max_examples=1000)
def test_valid_version_consistency(version_str):
    """valid_version should be consistent with packaging.version.parse"""
    result = vcs.valid_version(version_str)
    
    try:
        version.parse(version_str)
        packaging_accepts = True
    except InvalidVersion:
        packaging_accepts = False
    
    assert result == packaging_accepts, \
        f"valid_version('{version_str}') = {result}, but packaging.version says {packaging_accepts}"


# Test 5: valid_version should accept all valid PEP 440 versions
@given(st.sampled_from([
    "1.0.0", "2.1.3", "1.0.0a1", "1.0.0b2", "1.0.0rc1",
    "1.0.0.dev0", "1.0.0+local", "1!1.0.0", "0.0.0",
    "2020.1.1", "1.0", "1", "1.0.0.post1"
]))
def test_valid_version_accepts_valid(version_str):
    """valid_version should accept known valid PEP 440 versions"""
    assert vcs.valid_version(version_str), \
        f"valid_version incorrectly rejected valid version '{version_str}'"


# Test 6: valid_version should reject invalid versions
@given(st.sampled_from([
    "not_a_version", "1.0.0.0.0.0", "v1.0.0", "1.0-beta",
    "1.0.x", "", "1.0.0-alpha", "latest"
]))
def test_valid_version_rejects_invalid(version_str):
    """valid_version should reject known invalid versions"""
    assert not vcs.valid_version(version_str), \
        f"valid_version incorrectly accepted invalid version '{version_str}'"


# Test 7: get_repo should handle git+ prefix correctly
@given(st.text(min_size=1))
@settings(max_examples=500)  
def test_get_repo_git_plus_prefix(url):
    """URLs starting with git+ should have the prefix removed"""
    assume(not url.startswith('git+'))
    assume(not any(c in url for c in ['\n', '\r', '\0']))
    
    git_plus_url = f"git+{url}"
    result = vcs.get_repo(git_plus_url)
    
    # git+ prefix should be stripped
    if result is not None:
        assert not result.startswith('git+'), \
            f"get_repo('git+{url}') = '{result}' still has git+ prefix"


# Test 8: HTTPS GitHub URLs should get .git suffix if missing
@given(st.text(min_size=1).filter(lambda x: '/' in x and not x.endswith('.git')))
@settings(max_examples=500)
def test_get_repo_github_suffix(path):
    """https://github.com URLs without .git should get .git added"""
    assume(not any(c in path for c in ['\n', '\r', '\0', ' ']))
    
    url = f"https://github.com/{path}"
    result = vcs.get_repo(url)
    
    assert result == f"{url}.git", \
        f"get_repo('{url}') = '{result}', expected '{url}.git'"


if __name__ == "__main__":
    print("Running property-based tests for copier._vcs...")
    
    # Run tests manually for debugging
    test_get_repo_idempotence()
    test_get_repo_gh_prefix()
    test_get_repo_gl_prefix()
    test_valid_version_consistency()
    test_valid_version_accepts_valid()
    test_valid_version_rejects_invalid()
    test_get_repo_git_plus_prefix()
    test_get_repo_github_suffix()
    
    print("All manual test runs completed!")