import os
import sys

# Add virtual environment site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.asset as asset
from pyramid.path import package_path, package_name


def test_asset_spec_from_abspath_exact_package_path_bug():
    """Test potential bug when abspath equals the package path itself"""
    
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage('testpkg')
    
    # Mock package_path to return a known path
    base_path = '/base/testpkg'
    original_package_path = asset.package_path
    original_package_name = asset.package_name
    
    try:
        asset.package_path = lambda p: base_path
        asset.package_name = lambda p: p.__name__
        
        # Test 1: Pass the exact package directory path
        abspath = base_path  # No trailing slash
        result = asset.asset_spec_from_abspath(abspath, package)
        
        # The function adds os.path.sep to package_path, making it '/base/testpkg/'
        # Then checks if '/base/testpkg'.startswith('/base/testpkg/')
        # This will be False, so it returns abspath unchanged
        # But logically, the package directory IS part of the package!
        
        print(f"Test 1 - Package dir itself:")
        print(f"  Input abspath: {abspath}")
        print(f"  Package path: {base_path}")
        print(f"  Result: {result}")
        print(f"  Expected: testpkg: (empty) or similar")
        
        # We'd expect this to return 'testpkg:' or 'testpkg:.' 
        # but it returns the absolute path
        assert result == abspath, "Bug confirmed: package directory not recognized as part of package"
        
        # Test 2: File directly in package directory
        abspath2 = os.path.join(base_path, 'file.txt')
        result2 = asset.asset_spec_from_abspath(abspath2, package)
        print(f"\nTest 2 - File in package dir:")
        print(f"  Input abspath: {abspath2}")
        print(f"  Result: {result2}")
        print(f"  Expected: testpkg:file.txt")
        
        # This should work correctly
        assert result2 == 'testpkg:file.txt'
        
        print("\nBUG FOUND: asset_spec_from_abspath fails to recognize the package directory itself as part of the package!")
        
    finally:
        asset.package_path = original_package_path
        asset.package_name = original_package_name


def test_asset_spec_from_abspath_trailing_slash_inconsistency():
    """Test inconsistent behavior with trailing slashes"""
    
    class MockPackage:
        def __init__(self, name):
            self.__name__ = name
    
    package = MockPackage('mypkg')
    
    original_package_path = asset.package_path
    original_package_name = asset.package_name
    
    try:
        # Test with package_path returning path WITH trailing slash
        asset.package_name = lambda p: p.__name__
        
        # Scenario 1: package_path returns '/base/mypkg' (no trailing slash)
        asset.package_path = lambda p: '/base/mypkg'
        
        # The function adds os.path.sep, making it '/base/mypkg/'
        result1 = asset.asset_spec_from_abspath('/base/mypkg', package)
        result2 = asset.asset_spec_from_abspath('/base/mypkg/', package)
        result3 = asset.asset_spec_from_abspath('/base/mypkg/subdir', package)
        
        print("Scenario 1 - package_path without trailing slash:")
        print(f"  /base/mypkg -> {result1}")
        print(f"  /base/mypkg/ -> {result2}")
        print(f"  /base/mypkg/subdir -> {result3}")
        
        # Scenario 2: What if package_path already has trailing slash?
        asset.package_path = lambda p: '/base/mypkg/'
        
        # The function adds os.path.sep, making it '/base/mypkg//'
        result4 = asset.asset_spec_from_abspath('/base/mypkg', package)
        result5 = asset.asset_spec_from_abspath('/base/mypkg/', package)
        result6 = asset.asset_spec_from_abspath('/base/mypkg/subdir', package)
        
        print("\nScenario 2 - package_path with trailing slash:")
        print(f"  /base/mypkg -> {result4}")
        print(f"  /base/mypkg/ -> {result5}")
        print(f"  /base/mypkg/subdir -> {result6}")
        
    finally:
        asset.package_path = original_package_path
        asset.package_name = original_package_name


if __name__ == '__main__':
    print("Testing for bugs in pyramid.asset module...")
    print("=" * 60)
    
    try:
        test_asset_spec_from_abspath_exact_package_path_bug()
    except AssertionError as e:
        print(f"\nAssertion: {e}")
    
    print("\n" + "=" * 60)
    test_asset_spec_from_abspath_trailing_slash_inconsistency()