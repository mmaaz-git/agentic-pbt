import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.path import FSAssetDescriptor

# Check how other methods handle null bytes
path_with_null = "test\x00file"
descriptor = FSAssetDescriptor(path_with_null)

print(f"Path: {repr(path_with_null)}")
print(f"Descriptor path: {repr(descriptor.path)}")
print()

# Test each method
methods = ['exists', 'isdir', 'abspath', 'listdir']
for method_name in methods:
    method = getattr(descriptor, method_name)
    try:
        result = method()
        print(f"{method_name}(): {result}")
    except Exception as e:
        print(f"{method_name}(): RAISED {type(e).__name__}: {e}")