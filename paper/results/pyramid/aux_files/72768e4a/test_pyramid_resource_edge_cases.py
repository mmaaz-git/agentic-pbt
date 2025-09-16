#!/usr/bin/env python3
"""Focused property-based tests for edge cases in pyramid.resource/pyramid.asset module."""

import os
import sys

# Add the pyramid environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pyramid.asset as asset
import pyramid.resource as resource


# Test 1: Check behavior with multiple colons
@given(st.text(alphabet=st.characters(blacklist_characters='\x00/'), min_size=1).filter(lambda s: s.count(':') >= 2))
@settings(max_examples=1000)
def test_multiple_colons_in_spec(spec_with_multiple_colons):
    """Test resolve_asset_spec with multiple colons - should split on FIRST colon only."""
    assume(not os.path.isabs(spec_with_multiple_colons))
    
    pname, filename = asset.resolve_asset_spec(spec_with_multiple_colons)
    
    # Should split on the FIRST colon
    expected_pname, expected_filename = spec_with_multiple_colons.split(':', 1)
    assert pname == expected_pname
    assert filename == expected_filename
    
    # The filename part can contain colons
    assert ':' in filename if spec_with_multiple_colons.count(':') > 1 else True


# Test 2: Check behavior with empty strings
@given(st.sampled_from(['', ':', 'package:', ':filename']))
@settings(max_examples=100)
def test_empty_string_edge_cases(spec):
    """Test edge cases with empty strings and bare colons."""
    result_pname, result_filename = asset.resolve_asset_spec(spec)
    
    if spec == '':
        # Empty spec should return ('__main__', '') when pname='__main__' (default)
        # or (None, '') when pname=None
        assert result_filename == ''
    elif spec == ':':
        # Just a colon should split into ('', '')
        assert result_pname == ''
        assert result_filename == ''
    elif spec == 'package:':
        # Package with empty filename
        assert result_pname == 'package'
        assert result_filename == ''
    elif spec == ':filename':
        # Empty package with filename
        assert result_pname == ''
        assert result_filename == 'filename'


# Test 3: Unicode and special characters in paths
@given(
    st.text(alphabet=st.characters(min_codepoint=128, blacklist_characters='\x00/:'), min_size=1),
    st.text(alphabet=st.characters(min_codepoint=128, blacklist_characters='\x00/:'), min_size=1)
)
@settings(max_examples=500)
def test_unicode_in_spec(unicode_package, unicode_filename):
    """Test that Unicode characters are handled correctly in asset specs."""
    spec = f"{unicode_package}:{unicode_filename}"
    
    pname, filename = asset.resolve_asset_spec(spec)
    assert pname == unicode_package
    assert filename == unicode_filename


# Test 4: Check that resolve_asset_spec handles object with __name__ attribute correctly
@given(st.text(alphabet=st.characters(blacklist_characters='\x00/'), min_size=1))
@settings(max_examples=500)
def test_pname_object_with_name(filename):
    """Test that pname objects with __name__ are handled correctly."""
    assume(not os.path.isabs(filename))
    assume(':' not in filename)
    
    class CustomPackage:
        def __init__(self, name):
            self.__name__ = name
    
    test_names = ['test.package', '__main__', '', 'package:with:colons']
    
    for name in test_names:
        package = CustomPackage(name)
        pname, result_filename = asset.resolve_asset_spec(filename, package)
        assert pname == name
        assert result_filename == filename


# Test 5: Test with None package name
@given(st.text(alphabet=st.characters(blacklist_characters='\x00/'), min_size=1))
@settings(max_examples=500)
def test_none_package_name(filename):
    """Test behavior when pname is None."""
    assume(not os.path.isabs(filename))
    assume(':' not in filename)
    
    pname, result_filename = asset.resolve_asset_spec(filename, None)
    assert pname is None
    assert result_filename == filename


# Test 6: Windows-style absolute paths (if on Windows)
@given(st.sampled_from(['C:\\', 'D:\\', 'Z:\\']) if sys.platform == 'win32' else st.just('/'),
       st.lists(st.text(alphabet=st.characters(blacklist_characters='\x00/\\:'), min_size=1), min_size=0, max_size=3))
@settings(max_examples=100)
def test_windows_absolute_paths(drive, path_parts):
    """Test that Windows absolute paths are recognized correctly."""
    if sys.platform == 'win32':
        abspath = drive + '\\'.join(path_parts)
    else:
        abspath = '/' + '/'.join(path_parts)
    
    pname, filename = asset.resolve_asset_spec(abspath)
    assert pname is None
    assert filename == abspath


# Test 7: Test abspath_from_asset_spec with various inputs
@given(st.text(alphabet=st.characters(blacklist_characters='\x00'), min_size=1))
@settings(max_examples=500)
def test_abspath_from_asset_spec_edge_cases(spec):
    """Test abspath_from_asset_spec with various edge cases."""
    # Test with None pname
    result = asset.abspath_from_asset_spec(spec, None)
    assert result == spec
    
    # Test with __main__ pname and no colon in spec
    if ':' not in spec and not os.path.isabs(spec):
        result = asset.abspath_from_asset_spec(spec, '__main__')
        # Should use pkg_resources to resolve
        assert result is not None


# Test 8: Interaction between resolve_asset_spec and abspath_from_asset_spec
@given(st.text(alphabet=st.characters(blacklist_characters='\x00'), min_size=1))
@settings(max_examples=500)
def test_resolve_then_abspath(spec):
    """Test chaining resolve_asset_spec and abspath_from_asset_spec."""
    # First resolve
    pname, filename = asset.resolve_asset_spec(spec, '__main__')
    
    # Then get abspath
    if pname is None:
        # Absolute path case
        result = asset.abspath_from_asset_spec(filename, pname)
        assert result == filename
    else:
        # Package case
        result = asset.abspath_from_asset_spec(f"{pname}:{filename}", '__main__')
        assert result is not None


# Test 9: Special filesystem characters
@given(st.text(alphabet=st.sampled_from(['..', '.', '~', ' ', '\t', '\n', '\r']), min_size=1, max_size=10))
@settings(max_examples=500)
def test_special_filesystem_chars(special_chars):
    """Test with special filesystem characters."""
    if not os.path.isabs(special_chars):
        pname, filename = asset.resolve_asset_spec(special_chars)
        assert filename == special_chars
        
        # With colon
        if ':' not in special_chars:
            spec = f"package:{special_chars}"
            pname, filename = asset.resolve_asset_spec(spec)
            assert pname == 'package'
            assert filename == special_chars


# Test 10: Very long paths
@given(st.text(alphabet=st.characters(whitelist_categories=('Ll',)), min_size=1000, max_size=5000))
@settings(max_examples=10)
def test_very_long_paths(long_string):
    """Test with very long paths to check for buffer overflows or length limits."""
    # Test as filename
    pname, filename = asset.resolve_asset_spec(long_string, '__main__')
    assert pname == '__main__'
    assert filename == long_string
    
    # Test as package:filename
    spec = f"pkg:{long_string}"
    pname, filename = asset.resolve_asset_spec(spec)
    assert pname == 'pkg'
    assert filename == long_string


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])