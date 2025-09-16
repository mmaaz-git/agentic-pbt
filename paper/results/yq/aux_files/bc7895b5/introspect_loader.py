import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import inspect
import yq.loader

# Get all public functions and classes
members = inspect.getmembers(yq.loader, lambda x: not x.__name__.startswith('_') if hasattr(x, '__name__') else False)

print("=== Module Overview ===")
print(f"Module file: {yq.loader.__file__}")

print("\n=== Public Functions and Classes ===")
for name, obj in members:
    if inspect.isfunction(obj) or inspect.isclass(obj):
        print(f"\n{name}: {type(obj).__name__}")
        try:
            sig = inspect.signature(obj)
            print(f"  Signature: {sig}")
        except:
            pass
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Docstring: {obj.__doc__[:200]}")

# Test some key functions
print("\n=== Testing Key Functions ===")

# Test set_yaml_grammar
print("\nTesting set_yaml_grammar:")
import yaml
resolver = yaml.SafeLoader
try:
    yq.loader.set_yaml_grammar(resolver, "1.1")
    print("  ✓ set_yaml_grammar with version 1.1 works")
except Exception as e:
    print(f"  ✗ Error: {e}")

try:
    yq.loader.set_yaml_grammar(resolver, "1.2")
    print("  ✓ set_yaml_grammar with version 1.2 works")
except Exception as e:
    print(f"  ✗ Error: {e}")

# Test hash_key
print("\nTesting hash_key:")
test_key = "test_key"
result = yq.loader.hash_key(test_key)
print(f"  hash_key('{test_key}') = {result}")
print(f"  Type: {type(result)}")

# Test get_loader
print("\nTesting get_loader:")
loader = yq.loader.get_loader()
print(f"  Default loader type: {loader}")
loader_with_annotations = yq.loader.get_loader(use_annotations=True)
print(f"  Loader with annotations: {loader_with_annotations}")