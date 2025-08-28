#!/usr/bin/env /root/hypothesis-llm/envs/pyramid_env/bin/python
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
import pyramid.predicates

# Get all classes and functions
members = inspect.getmembers(pyramid.predicates)
classes = [m for m in members if inspect.isclass(m[1]) and m[1].__module__ == 'pyramid.predicates']
functions = [m for m in members if inspect.isfunction(m[1]) and m[1].__module__ == 'pyramid.predicates']

print("Classes in pyramid.predicates:")
for name, cls in classes:
    print(f"  {name}")
    if hasattr(cls, '__init__'):
        sig = inspect.signature(cls.__init__)
        print(f"    __init__{sig}")
    if hasattr(cls, '__call__'):
        sig = inspect.signature(cls.__call__)
        print(f"    __call__{sig}")
    if hasattr(cls, 'text'):
        print(f"    text() method present")
    if hasattr(cls, 'phash'):
        print(f"    phash method/property present")
    print()

print("Functions in pyramid.predicates:")
for name, func in functions:
    sig = inspect.signature(func)
    print(f"  {name}{sig}")