import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.registry

# Get all classes and functions in the module
members = inspect.getmembers(pyramid.registry)

print("Classes:")
for name, obj in members:
    if inspect.isclass(obj) and obj.__module__ == 'pyramid.registry':
        print(f"  {name}: {obj.__doc__[:80] if obj.__doc__ else 'No doc'}")
        # List methods
        methods = [m for m in dir(obj) if not m.startswith('_') or m.startswith('__init__')]
        print(f"    Methods: {', '.join(methods[:10])}")
        
print("\nFunctions:")
for name, obj in members:
    if inspect.isfunction(obj) and obj.__module__ == 'pyramid.registry':
        print(f"  {name}: {inspect.signature(obj)}")
        print(f"    Doc: {obj.__doc__[:80] if obj.__doc__ else 'No doc'}")

# Let's examine the Registry class more closely
Registry = pyramid.registry.Registry
print("\n\nRegistry class:")
print(f"  Signature: {inspect.signature(Registry.__init__)}")
print(f"  Base classes: {Registry.__bases__}")

# Look at Introspector class
Introspector = pyramid.registry.Introspector
print("\n\nIntrospector class:")
print(f"  Signature: {inspect.signature(Introspector.__init__)}")
print("  Methods:")
for method_name in ['add', 'get', 'get_category', 'remove', 'relate', 'unrelate']:
    if hasattr(Introspector, method_name):
        method = getattr(Introspector, method_name)
        print(f"    {method_name}: {inspect.signature(method)}")

# Introspectable class
Introspectable = pyramid.registry.Introspectable
print("\n\nIntrospectable class:")
print(f"  Signature: {inspect.signature(Introspectable.__init__)}")
print("  Methods:")
for method_name in ['relate', 'unrelate', 'register']:
    if hasattr(Introspectable, method_name):
        method = getattr(Introspectable, method_name)
        print(f"    {method_name}: {inspect.signature(method)}")

# Deferred class
Deferred = pyramid.registry.Deferred
print("\n\nDeferred class:")
print(f"  Signature: {inspect.signature(Deferred.__init__)}")
print(f"  Methods: {[m for m in dir(Deferred) if not m.startswith('_')]}")