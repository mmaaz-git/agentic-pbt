import os
import sys

# Add virtual environment site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pyramid.asset as asset
from pyramid.path import package_name


# Property-based test that reveals the bug
@given(
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10),
    st.booleans()
)
def test_asset_spec_from_abspath_package_dir_bug(pkg_name, with_trailing_slash):
    """Property: The package directory itself should be recognized as part of the package"""
    
    if pkg_name == '__main__':
        # Skip __main__ as it has special behavior
        return
    
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage(pkg_name)
    
    # Mock the dependencies
    base_path = f'/test/{pkg_name}'
    original_package_path = asset.package_path
    original_package_name = asset.package_name
    
    try:
        asset.package_path = lambda p: base_path
        asset.package_name = lambda p: p.__name__
        
        # Test the package directory path itself
        if with_trailing_slash:
            abspath = base_path + '/'
        else:
            abspath = base_path
        
        result = asset.asset_spec_from_abspath(abspath, package)
        
        # Property: A path that represents the package directory itself 
        # should be recognized as part of the package and return an asset spec
        # not the absolute path
        
        # Currently, when abspath = base_path (no trailing slash), 
        # the function returns the absolute path instead of an asset spec
        # This is inconsistent with the behavior when there's a trailing slash
        
        if with_trailing_slash:
            # With trailing slash, it correctly returns 'pkg_name:'
            assert result == f"{pkg_name}:", f"With trailing slash: expected '{pkg_name}:', got '{result}'"
        else:
            # Without trailing slash, it incorrectly returns the absolute path
            # This is the bug!
            assert result == abspath, f"Bug confirmed: without trailing slash, returns absolute path '{result}' instead of asset spec"
            # The correct behavior would be: assert result == f"{pkg_name}:" or similar
            
    finally:
        asset.package_path = original_package_path
        asset.package_name = original_package_name


@given(
    st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')), min_size=1, max_size=10),
)
def test_asset_spec_trailing_slash_in_package_path(pkg_name):
    """Test bug when package_path returns a path with trailing slash"""
    
    if pkg_name == '__main__':
        return
        
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage(pkg_name)
    
    # If package_path returns a path WITH trailing slash already
    base_path_with_slash = f'/test/{pkg_name}/'
    original_package_path = asset.package_path
    original_package_name = asset.package_name
    
    try:
        # Mock package_path to return path WITH trailing slash
        asset.package_path = lambda p: base_path_with_slash
        asset.package_name = lambda p: p.__name__
        
        # The function will add another os.path.sep, making it '/test/pkg//'
        # This double slash breaks the startswith check
        
        test_file = f'/test/{pkg_name}/file.txt'
        result = asset.asset_spec_from_abspath(test_file, package)
        
        # This should return 'pkg_name:file.txt' but due to the double slash bug,
        # it returns the absolute path unchanged
        assert result == test_file, f"Bug confirmed: double slash prevents recognition"
        
    finally:
        asset.package_path = original_package_path
        asset.package_name = original_package_name


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])