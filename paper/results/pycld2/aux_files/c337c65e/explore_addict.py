#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

from addict import Dict
import inspect

# Get Dict class methods and docstrings
print("Dict class documentation:")
print(Dict.__doc__)
print("\n" + "="*60 + "\n")

print("Dict methods and their signatures:")
for name in dir(Dict):
    if not name.startswith('_') or name in ['__init__', '__setitem__', '__getitem__', '__missing__']:
        try:
            method = getattr(Dict, name)
            if callable(method):
                sig = inspect.signature(method) if hasattr(inspect, 'signature') else None
                doc = method.__doc__
                print(f"\n{name}{sig if sig else '()'}")
                if doc:
                    print(f"  Doc: {doc.split(chr(10))[0][:100]}")
        except:
            pass

print("\n" + "="*60 + "\n")
print("Testing basic Dict functionality:")

# Test basic creation and access
d = Dict()
print(f"Empty dict: {d}")

d.foo = 'bar'
print(f"After d.foo = 'bar': {d}")

d['baz'] = 'qux'
print(f"After d['baz'] = 'qux': {d}")

# Test nested access
d.nested.deep.value = 42
print(f"After d.nested.deep.value = 42: {d}")

# Test from existing dict
existing = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
d2 = Dict(existing)
print(f"\nDict from existing: {d2}")
print(f"Access d2.b.d.e: {d2.b.d.e}")

# Test freezing
d3 = Dict({'x': 1})
d3.freeze()
print(f"\nFrozen dict: {d3}")
try:
    d3.y = 2
    print("Should not reach here - frozen dict allowed new key")
except KeyError as e:
    print(f"Frozen dict correctly raised KeyError for new key: {e}")
    
# Test to_dict
d4 = Dict({'a': {'b': {'c': 1}}})
regular = d4.to_dict()
print(f"\nDict type: {type(d4.a)}")
print(f"After to_dict type: {type(regular['a'])}")