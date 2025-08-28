import os
import sys

# Add virtual environment site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis import HealthCheck
import pyramid.asset as asset
from pyramid.path import package_path


# Test for potential bug: asset_spec_from_abspath with paths that start with but aren't in package
@given(
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10),
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10)
)
def test_asset_spec_from_abspath_prefix_bug(package_suffix, extra_suffix):
    """Test for potential prefix matching bug in asset_spec_from_abspath"""
    
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage('testpkg')
    
    # Mock package_path to return /base/test
    base_path = '/base/test'
    original_package_path = asset.package_path
    
    try:
        asset.package_path = lambda p: base_path
        
        # Create a path that starts with base_path but isn't inside it
        # e.g., /base/test vs /base/testextra/file.txt
        abspath = base_path + extra_suffix + '/' + package_suffix
        result = asset.asset_spec_from_abspath(abspath, package)
        
        # Check if it incorrectly thinks this is inside the package
        if not abspath.startswith(base_path + os.path.sep):
            # This path is NOT inside the package, should return abspath unchanged
            assert result == abspath, f"Bug: incorrectly treated {abspath} as inside {base_path}"
        
    finally:
        asset.package_path = original_package_path


# Test empty string edge cases
@given(st.sampled_from(['', ':', '::', 'pkg:', ':file', '::file']))
def test_resolve_asset_spec_empty_edge_cases(spec):
    """Test edge cases with empty strings and colons"""
    result_pname, result_filename = asset.resolve_asset_spec(spec)
    
    # Verify the function doesn't crash and returns something sensible
    if ':' in spec:
        parts = spec.split(':', 1)
        # If there's a colon, first part should be package name (or empty)
        assert result_pname == parts[0]
        assert result_filename == parts[1]
    else:
        assert result_filename == spec


# Test with None as pname
def test_resolve_asset_spec_none_pname():
    """Test that None as pname is handled correctly"""
    result_pname, result_filename = asset.resolve_asset_spec('test.txt', pname=None)
    assert result_pname is None
    assert result_filename == 'test.txt'
    
    # Test with colon in spec and None pname
    result_pname, result_filename = asset.resolve_asset_spec('pkg:test.txt', pname=None)
    assert result_pname == 'pkg'
    assert result_filename == 'test.txt'


# Test path normalization edge cases with os.path.sep
@given(
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10),
    st.lists(st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=5), min_size=1, max_size=3)
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_asset_spec_path_separator_edge_cases(package_name, path_parts):
    """Test edge cases in path separator handling"""
    
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage(package_name)
    
    # Create path with OS-specific separators
    relpath = os.path.sep.join(path_parts)
    base_path = f'/base/{package_name}'
    
    original_package_path = asset.package_path
    
    try:
        asset.package_path = lambda p: base_path
        
        # Test with path inside package
        abspath = base_path + os.path.sep + relpath
        result = asset.asset_spec_from_abspath(abspath, package)
        
        # Should have forward slashes regardless of OS
        expected_relpath = '/'.join(path_parts)
        expected = f"{package_name}:{expected_relpath}"
        assert result == expected
        
    finally:
        asset.package_path = original_package_path


# Test potential integer/string confusion
def test_resolve_asset_spec_with_numeric_pname():
    """Test that numeric types are handled correctly for pname"""
    # The code converts non-string pname to pname.__name__
    class NumericMock:
        __name__ = 42  # Not a string!
    
    try:
        result = asset.resolve_asset_spec('test.txt', pname=NumericMock())
        # This might cause an error if the code doesn't handle non-string __name__
    except (AttributeError, TypeError) as e:
        # If this raises an error, it's a potential bug
        print(f"Potential bug: pname with numeric __name__ causes: {e}")
        raise


# Test special characters in package names and paths
@given(
    st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs']), min_size=1, max_size=20).filter(lambda s: ':' not in s and s.strip()),
    st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs']), min_size=1, max_size=20).filter(lambda s: s.strip())
)
@settings(max_examples=50)
def test_unicode_and_special_chars(package_name, file_path):
    """Test handling of unicode and special characters"""
    if ':' in file_path:
        # Skip if file_path contains colon as it would change the parsing
        assume(False)
    
    spec = f"{package_name}:{file_path}"
    
    try:
        result_pname, result_filename = asset.resolve_asset_spec(spec)
        assert result_pname == package_name
        assert result_filename == file_path
    except Exception as e:
        print(f"Failed with package_name={repr(package_name)}, file_path={repr(file_path)}")
        raise


# Test abspath_from_asset_spec backward compatibility function
@given(
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10),
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10)
)
def test_abspath_from_asset_spec_with_none(package_name, filename):
    """Test the backward compatibility function with None pname"""
    # Test with None - should return spec unchanged
    spec = f"{package_name}:{filename}"
    result = asset.abspath_from_asset_spec(spec, pname=None)
    assert result == spec
    
    # Test absolute path with None
    abs_spec = f"/{filename}"
    result = asset.abspath_from_asset_spec(abs_spec, pname=None)
    assert result == abs_spec