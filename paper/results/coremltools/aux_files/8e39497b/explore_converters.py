import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import inspect
import coremltools.converters as converters

# Focus on main convert function
print("=== Main convert function ===")
print("Signature:", inspect.signature(converters.convert))
print("\nDocstring (first 1000 chars):")
print(converters.convert.__doc__[:1000] if converters.convert.__doc__ else "No docstring")

# Explore shape-related classes
print("\n\n=== Shape and Dimension Classes ===")
for cls_name in ['Shape', 'RangeDim', 'EnumeratedShapes']:
    if hasattr(converters, cls_name):
        cls = getattr(converters, cls_name)
        print(f"\n{cls_name}:")
        print(f"  Type: {type(cls)}")
        if hasattr(cls, '__doc__'):
            doc = cls.__doc__
            if doc:
                print(f"  Doc (first 500 chars): {doc[:500]}")

# Explore type classes
print("\n\n=== Type Classes ===")
for cls_name in ['TensorType', 'ImageType', 'StateType']:
    if hasattr(converters, cls_name):
        cls = getattr(converters, cls_name)
        print(f"\n{cls_name}:")
        print(f"  Type: {type(cls)}")
        if hasattr(cls, '__init__'):
            try:
                print(f"  Init signature: {inspect.signature(cls.__init__)}")
            except:
                pass
        if hasattr(cls, '__doc__'):
            doc = cls.__doc__
            if doc:
                print(f"  Doc (first 500 chars): {doc[:500]}")