#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import inspect
import awkward
import awkward.prettyprint as pp

# Get all public functions/classes in prettyprint module
print("=== Public members in awkward.prettyprint ===")
members = inspect.getmembers(pp, lambda x: not x.__name__.startswith('_') if hasattr(x, '__name__') else False)
for name, obj in members:
    if inspect.isfunction(obj) or inspect.isclass(obj):
        print(f"\n{name}: {type(obj).__name__}")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Docstring: {obj.__doc__[:200]}...")
        try:
            sig = inspect.signature(obj)
            print(f"  Signature: {sig}")
        except:
            pass

# Check specific functions that look interesting
print("\n\n=== Detailed analysis of key functions ===")

print("\n1. half function:")
print(f"  Signature: {inspect.signature(pp.half)}")
print(f"  Source:\n{inspect.getsource(pp.half)}")

print("\n2. alternate function:")
print(f"  Signature: {inspect.signature(pp.alternate)}")
print(f"  Source:\n{inspect.getsource(pp.alternate)}")

print("\n3. bytes_repr function:")
print(f"  Signature: {inspect.signature(pp.bytes_repr)}")
print(f"  Source:\n{inspect.getsource(pp.bytes_repr)}")