import os
import sys

# Add virtual environment site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import tempfile
from hypothesis import given, strategies as st, assume
import pyramid.asset as asset
from pyramid.path import package_path


# Strategy for package names
package_names = st.text(
    alphabet=st.characters(
        min_codepoint=ord('a'), 
        max_codepoint=ord('z')
    ) | st.sampled_from(['_', '.']),
    min_size=1,
    max_size=20
).filter(lambda s: not s.startswith('.') and not s.endswith('.') and '..' not in s)

# Strategy for file paths
file_paths = st.text(
    alphabet=st.characters(
        min_codepoint=ord('a'), 
        max_codepoint=ord('z')
    ) | st.sampled_from(['_', '/', '-']),
    min_size=1,
    max_size=30
).filter(lambda s: not s.startswith('/') and '//' not in s)


@given(package_names, file_paths)
def test_resolve_asset_spec_with_colon(package_name, file_path):
    """Test that resolve_asset_spec correctly parses specs with colons"""
    spec = f"{package_name}:{file_path}"
    result_pname, result_filename = asset.resolve_asset_spec(spec)
    assert result_pname == package_name
    assert result_filename == file_path


@given(file_paths)
def test_resolve_asset_spec_without_colon(file_path):
    """Test that resolve_asset_spec handles specs without colons"""
    assume(':' not in file_path)
    
    # Test with default pname
    result_pname, result_filename = asset.resolve_asset_spec(file_path)
    assert result_pname == '__main__'
    assert result_filename == file_path
    
    # Test with custom pname
    custom_pname = 'mypackage'
    result_pname, result_filename = asset.resolve_asset_spec(file_path, pname=custom_pname)
    assert result_pname == custom_pname
    assert result_filename == file_path


# Strategy for absolute paths
absolute_paths = st.text(
    alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')) | st.sampled_from(['/', '_', '-']),
    min_size=2,
    max_size=30
).map(lambda s: '/' + s.lstrip('/'))

@given(absolute_paths)
def test_resolve_asset_spec_absolute_paths(path):
    """Test that absolute paths are handled correctly"""
    assert os.path.isabs(path)
    result_pname, result_filename = asset.resolve_asset_spec(path)
    assert result_pname is None
    assert result_filename == path


@given(file_paths)
def test_asset_spec_from_abspath_main_package(relpath):
    """Test asset_spec_from_abspath with __main__ package"""
    # Create a mock package with __main__ name
    class MockPackage:
        __name__ = '__main__'
    
    # Any absolute path should be returned as-is for __main__
    abspath = os.path.join('/some/path', relpath)
    result = asset.asset_spec_from_abspath(abspath, MockPackage())
    assert result == abspath


@given(
    package_names.filter(lambda n: n != '__main__' and '.' not in n),
    file_paths
)
def test_asset_spec_from_abspath_path_separator_normalization(package_name, relpath):
    """Test that path separators are normalized correctly"""
    # Create a mock package
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage(package_name)
    
    # Mock the package_path function to return a known path
    base_path = f'/base/{package_name}'
    original_package_path = asset.package_path
    
    try:
        # Temporarily replace package_path
        asset.package_path = lambda p: base_path
        
        # Create an absolute path within the package
        abspath = os.path.join(base_path, relpath)
        result = asset.asset_spec_from_abspath(abspath, package)
        
        # The result should be package:relpath with forward slashes
        expected = f"{package_name}:{relpath.replace(os.path.sep, '/')}"
        assert result == expected
        
    finally:
        # Restore original function
        asset.package_path = original_package_path


@given(
    package_names.filter(lambda n: n != '__main__' and '.' not in n),
    file_paths
)
def test_asset_spec_from_abspath_outside_package(package_name, relpath):
    """Test that paths outside the package directory are returned as-is"""
    # Create a mock package
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage(package_name)
    
    # Mock the package_path function
    base_path = f'/base/{package_name}'
    original_package_path = asset.package_path
    
    try:
        asset.package_path = lambda p: base_path
        
        # Create an absolute path OUTSIDE the package
        abspath = f'/different/path/{relpath}'
        result = asset.asset_spec_from_abspath(abspath, package)
        
        # Should return the absolute path unchanged
        assert result == abspath
        
    finally:
        asset.package_path = original_package_path


@given(st.data())
def test_resolve_asset_spec_with_module_objects(data):
    """Test that pname can be a module object, not just a string"""
    # Create a mock module
    class MockModule:
        __name__ = data.draw(package_names)
    
    module = MockModule()
    file_path = data.draw(file_paths)
    
    # Test with module object as pname
    result_pname, result_filename = asset.resolve_asset_spec(file_path, pname=module)
    assert result_pname == module.__name__
    assert result_filename == file_path


@given(package_names, file_paths)
def test_spec_parsing_edge_cases(package_name, file_path):
    """Test edge cases in spec parsing with multiple colons"""
    # Test spec with multiple colons - should split on first colon only
    spec = f"{package_name}:{file_path}:extra:colons"
    result_pname, result_filename = asset.resolve_asset_spec(spec)
    assert result_pname == package_name
    assert result_filename == f"{file_path}:extra:colons"


@given(st.text(min_size=0, max_size=100))
def test_empty_spec_handling(spec):
    """Test handling of empty or special specs"""
    if ':' in spec:
        parts = spec.split(':', 1)
        expected_pname = parts[0] if parts[0] else parts[0]  # Empty string stays empty
        expected_filename = parts[1]
    else:
        expected_pname = '__main__'
        expected_filename = spec
    
    if os.path.isabs(spec):
        expected_pname = None
        expected_filename = spec
    
    result_pname, result_filename = asset.resolve_asset_spec(spec)
    assert result_pname == expected_pname
    assert result_filename == expected_filename