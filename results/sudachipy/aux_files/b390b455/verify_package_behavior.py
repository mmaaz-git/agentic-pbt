import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.path import AssetResolver

# Test with actual package (importlib is a package)
print("Testing with package (importlib):")
resolver = AssetResolver(package='importlib')
descriptor = resolver.resolve('test.txt')
print(f"  Input package: importlib")
print(f"  Result package: {descriptor.pkg_name}")
print(f"  Match: {descriptor.pkg_name == 'importlib'}")

# Test with module (importlib.machinery is a module)
print("\nTesting with module (importlib.machinery):")
resolver = AssetResolver(package='importlib.machinery')
descriptor = resolver.resolve('test.txt')
print(f"  Input: importlib.machinery")
print(f"  Result package: {descriptor.pkg_name}")
print(f"  This is expected per documentation - modules resolve to their containing package")

# Test with another package
print("\nTesting with package (urllib):")
import urllib
print(f"  urllib has __path__? {hasattr(urllib, '__path__')}")
resolver = AssetResolver(package='urllib')
descriptor = resolver.resolve('test.txt')
print(f"  Input package: urllib")
print(f"  Result package: {descriptor.pkg_name}")
print(f"  Match: {descriptor.pkg_name == 'urllib'}")