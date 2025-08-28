#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import inspect
import testpath

print("=== Module Overview ===")
print(f"Module: {testpath.__name__}")
print(f"Version: {testpath.__version__}")
print(f"Module file: {testpath.__file__}")

print("\n=== Exported Functions/Classes ===")
all_members = inspect.getmembers(testpath)
for name, obj in all_members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  {name}: {obj_type}")
        if callable(obj) and hasattr(obj, '__doc__') and obj.__doc__:
            docstring = obj.__doc__.strip().split('\n')[0]
            print(f"    Doc: {docstring}")

print("\n=== Key Functions Analysis ===")

# Analyze assert functions from asserts module
import testpath.asserts
print("\nAssertion functions:")
for name in dir(testpath.asserts):
    if name.startswith('assert_'):
        func = getattr(testpath.asserts, name)
        if callable(func):
            print(f"\n{name}:")
            sig = inspect.signature(func)
            print(f"  Signature: {sig}")
            if func.__doc__:
                print(f"  Doc: {func.__doc__.strip().split('\\n')[0]}")

# Analyze MockCommand
print("\n\nMockCommand class:")
print(f"  Signature: {inspect.signature(testpath.MockCommand.__init__)}")
if testpath.MockCommand.__doc__:
    print(f"  Doc: {testpath.MockCommand.__doc__.strip().split('\\n')[0]}")

# Analyze environment functions
print("\n\nEnvironment functions:")
for name in ['temporary_env', 'modified_env', 'make_env_restorer']:
    func = getattr(testpath, name)
    print(f"\n{name}:")
    sig = inspect.signature(func)
    print(f"  Signature: {sig}")
    if func.__doc__:
        print(f"  Doc: {func.__doc__.strip().split('\\n')[0]}")