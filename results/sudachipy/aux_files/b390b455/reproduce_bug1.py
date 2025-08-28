import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.path import AssetResolver

# Bug: AssetResolver changes the package name from a submodule to its parent package
resolver = AssetResolver(package='importlib.machinery')
descriptor = resolver.resolve('test.txt')

print(f"Expected package: importlib.machinery")
print(f"Actual package:   {descriptor.pkg_name}")
print(f"Bug confirmed:    {descriptor.pkg_name != 'importlib.machinery'}")
print(f"Asset spec:       {descriptor.absspec()}")