import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yaml
import yq.loader

print("=== Investigating loader class hierarchy ===")

# Test the failing case
loader_class = yq.loader.get_loader(
    use_annotations=False,
    expand_aliases=True,
    expand_merge_keys=False
)

print(f"Loader class returned: {loader_class}")
print(f"Loader class MRO: {loader_class.__mro__}")

print(f"\nyaml.SafeLoader: {yaml.SafeLoader}")
print(f"yaml.SafeLoader MRO: {yaml.SafeLoader.__mro__}")

try:
    from yaml import CSafeLoader
    print(f"\nCSafeLoader: {CSafeLoader}")
    print(f"CSafeLoader MRO: {CSafeLoader.__mro__}")
except ImportError:
    print("CSafeLoader not available")

print(f"\nCustomLoader: {yq.loader.CustomLoader}")
print(f"CustomLoader MRO: {yq.loader.CustomLoader.__mro__}")

# Check default_loader
print(f"\ndefault_loader in yq.loader: {yq.loader.default_loader}")

# Let's check what the code actually does
print("\n=== Code analysis ===")
print("Lines 16-19 in loader.py:")
print("try:")
print("    from yaml import CSafeLoader as default_loader")
print("except ImportError:")
print("    from yaml import SafeLoader as default_loader")

print("\nLine 199 in get_loader function:")
print("loader_class = default_loader if expand_aliases else CustomLoader")

# Test different combinations
print("\n=== Testing different parameter combinations ===")
for expand_aliases in [True, False]:
    loader = yq.loader.get_loader(expand_aliases=expand_aliases)
    print(f"expand_aliases={expand_aliases}: {loader}")