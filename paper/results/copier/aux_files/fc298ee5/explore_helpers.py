#!/usr/bin/env python3
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import copier._main
import copier._tools

# Let's look at the _tools module which has helper functions
print("=== Functions in copier._tools ===")
for name, obj in inspect.getmembers(copier._tools):
    if not name.startswith('_') and inspect.isfunction(obj):
        sig = inspect.signature(obj)
        doc = (obj.__doc__ or "").split('\n')[0][:100] if obj.__doc__ else "No doc"
        print(f"\n{name}{sig}")
        print(f"  Doc: {doc}")

# Look at functions that do path manipulation
print("\n=== Path-related functions in _main ===")
path_funcs = ['escape_git_path', 'normalize_git_path']
for func_name in path_funcs:
    func = getattr(copier._main, func_name, None)
    if func:
        print(f"\n{func_name}:")
        print(f"  Signature: {inspect.signature(func)}")
        # Try to see if we can get the source
        try:
            source = inspect.getsource(func)
            # Show first few lines
            lines = source.split('\n')[:10]
            print("  Source (first 10 lines):")
            for line in lines:
                print(f"    {line}")
        except:
            print("  Source not available")

# Look at the cast_to_bool function
print("\n=== cast_to_bool function ===")
func = copier._main.cast_to_bool
print(f"Signature: {inspect.signature(func)}")
try:
    source = inspect.getsource(func)
    print("Source:")
    for line in source.split('\n'):
        print(f"  {line}")
except:
    print("Source not available")