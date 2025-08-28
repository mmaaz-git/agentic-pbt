import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.path import FSAssetDescriptor

# Bug: FSAssetDescriptor.listdir() crashes on paths with null bytes
path_with_null = "test\x00file"
descriptor = FSAssetDescriptor(path_with_null)

print(f"Path: {repr(path_with_null)}")
print(f"Descriptor path: {repr(descriptor.path)}")

try:
    result = descriptor.listdir()
    print(f"Result: {result}")
except ValueError as e:
    print(f"Error raised: {e}")
    print("Bug confirmed: listdir() crashes on null bytes in path")