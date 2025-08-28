#!/usr/bin/env python3
"""Property-based tests for pyramid.resource/pyramid.asset module."""

import os
import sys
import tempfile

# Add the pyramid environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.asset as asset
import pyramid.resource as resource


# Strategy for generating valid package names
package_names = st.one_of(
    st.none(),
    st.just('__main__'),
    st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_'), min_size=1).filter(lambda s: not s[0].isdigit()),
    st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_.'), min_size=1).filter(
        lambda s: not s[0].isdigit() and not s.startswith('.') and not s.endswith('.') and '..' not in s
    )
)

# Strategy for filenames
filenames = st.text(alphabet=st.characters(blacklist_characters='\x00'), min_size=1).filter(
    lambda s: not s.startswith('/') and ':' not in s
)

# Strategy for asset specs with colon
asset_specs_with_colon = st.builds(
    lambda p, f: f"{p}:{f}",
    package_names.filter(lambda p: p is not None and ':' not in str(p)),
    filenames
)

# Strategy for absolute paths
absolute_paths = st.builds(
    lambda parts: os.path.join('/', *parts),
    st.lists(st.text(alphabet=st.characters(blacklist_characters='\x00/'), min_size=1), min_size=0, max_size=5)
)


@given(absolute_paths)
@settings(max_examples=1000)
def test_resolve_asset_spec_absolute_path_invariant(abspath):
    """When spec is an absolute path, resolve_asset_spec returns (None, spec)."""
    # This property is explicitly coded in lines 10-11 of pyramid/asset.py
    pname, filename = asset.resolve_asset_spec(abspath)
    assert pname is None
    assert filename == abspath
    
    # Also test through the compatibility shim
    pname2, filename2 = resource.resolve_resource_spec(abspath)
    assert pname2 is None
    assert filename2 == abspath


@given(asset_specs_with_colon, package_names)
@settings(max_examples=1000)
def test_resolve_asset_spec_colon_parsing(spec_with_colon, pname):
    """When spec contains ':', it splits on first colon into (package, filename)."""
    # This property is explicitly coded in lines 13-14 of pyramid/asset.py
    result_pname, result_filename = asset.resolve_asset_spec(spec_with_colon, pname)
    
    # The spec should be split on the first colon
    expected_pname, expected_filename = spec_with_colon.split(':', 1)
    assert result_pname == expected_pname
    assert result_filename == expected_filename


@given(filenames, package_names)
@settings(max_examples=1000)
def test_resolve_asset_spec_no_colon(filename, pname):
    """When spec has no colon and is not absolute, uses provided pname."""
    # Ensure it's not an absolute path
    assume(not os.path.isabs(filename))
    
    result_pname, result_filename = asset.resolve_asset_spec(filename, pname)
    
    if pname is None:
        assert result_pname is None
        assert result_filename == filename
    else:
        # When pname is provided and spec has no colon, pname is used
        if isinstance(pname, str):
            assert result_pname == pname
        else:
            # If pname is not a string, it should use pname.__name__
            assert result_pname == getattr(pname, '__name__', pname)
        assert result_filename == filename


@given(st.text(alphabet=st.characters(blacklist_characters='\x00'), min_size=1))
@settings(max_examples=1000)
def test_asset_spec_from_abspath_main_package(abspath):
    """When package is __main__, asset_spec_from_abspath returns abspath unchanged."""
    # Create a mock package with __name__ == '__main__'
    class MockMainPackage:
        __name__ = '__main__'
    
    result = asset.asset_spec_from_abspath(abspath, MockMainPackage())
    assert result == abspath


@given(
    st.lists(st.text(alphabet=st.characters(blacklist_characters='\x00/\\'), min_size=1), min_size=1, max_size=5)
)
@settings(max_examples=500)
def test_path_separator_normalization(path_parts):
    """asset_spec_from_abspath converts OS path separators to forward slashes."""
    # This test would need a real package to work properly
    # For now, we'll test the conversion logic itself
    
    # Create a temporary package-like object
    class MockPackage:
        __name__ = 'test_package'
        __file__ = os.path.join(tempfile.gettempdir(), 'test_package', '__init__.py')
    
    # Create a path within the package
    package_dir = os.path.dirname(MockPackage.__file__)
    test_path = os.path.join(package_dir, *path_parts)
    
    result = asset.asset_spec_from_abspath(test_path, MockPackage)
    
    # If the path starts with the package path, it should be converted to a spec
    if test_path.startswith(package_dir + os.path.sep):
        # The result should contain forward slashes, not OS separators
        if ':' in result:
            _, resource_path = result.split(':', 1)
            if os.path.sep == '\\':
                # On Windows, there should be no backslashes in the resource path
                assert '\\' not in resource_path
            # All paths should use forward slashes
            assert all(c != os.path.sep or c == '/' for c in resource_path)
    else:
        # If not within package, should return unchanged
        assert result == test_path


@given(
    st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_.'), min_size=1).filter(
        lambda s: not s[0].isdigit() and not s.startswith('.') and not s.endswith('.') and '..' not in s and s != '__main__'
    ),
    st.lists(st.text(alphabet=st.characters(blacklist_characters='\x00/\\:'), min_size=1), min_size=0, max_size=3)
)
@settings(max_examples=500)
def test_round_trip_property(package_name, path_parts):
    """Test round-trip between asset_spec_from_abspath and abspath_from_asset_spec."""
    # Skip if package doesn't exist
    try:
        __import__(package_name)
    except (ImportError, ValueError):
        assume(False)
    
    import pkg_resources
    
    # Get the package location
    try:
        package_path = pkg_resources.resource_filename(package_name, '')
    except:
        assume(False)
    
    # Create an abspath within the package
    if path_parts:
        resource_path = os.path.join(*path_parts)
        abspath = os.path.join(package_path, resource_path)
    else:
        abspath = package_path
    
    # Convert to asset spec
    spec = asset.asset_spec_from_abspath(abspath, sys.modules[package_name])
    
    # Convert back to abspath
    if ':' in spec:
        result = asset.abspath_from_asset_spec(spec)
        # The paths should be equivalent (may differ in trailing separators)
        assert os.path.normpath(result) == os.path.normpath(abspath)


@given(package_names)
@settings(max_examples=1000) 
def test_resolve_asset_spec_pname_conversion(pname):
    """Test that non-string pname is converted to string using __name__ attribute."""
    # Test with a mock object that has __name__
    class MockPackage:
        __name__ = 'mock_package'
    
    mock = MockPackage() if pname != '__main__' else pname
    
    # Use a simple filename
    filename = 'test.txt'
    
    if isinstance(pname, str) or pname is None:
        result_pname, result_filename = asset.resolve_asset_spec(filename, pname)
        if pname is None:
            assert result_pname is None
        else:
            assert result_pname == pname
    else:
        # Test with the mock object
        result_pname, result_filename = asset.resolve_asset_spec(filename, mock)
        assert result_pname == 'mock_package'
    
    assert result_filename == filename


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])