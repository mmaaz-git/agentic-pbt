#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import inspect
import fixit.rules

# Get all members of fixit.rules
members = inspect.getmembers(fixit.rules, lambda x: not (hasattr(x, '__name__') and x.__name__.startswith('_')))
print(f"Members of fixit.rules: {len(members)}")

# Get all rule modules
for name, obj in members:
    if inspect.ismodule(obj):
        print(f"Module: {name}")
    elif inspect.isclass(obj):
        print(f"Class: {name}")
        # Get signature if it has an __init__
        try:
            sig = inspect.signature(obj.__init__)
            print(f"  Signature: {sig}")
        except:
            pass
        # Get docstring
        if obj.__doc__:
            doc_lines = obj.__doc__.strip().split('\n')
            print(f"  Doc: {doc_lines[0][:100]}")
    elif callable(obj):
        print(f"Function: {name}")
        try:
            sig = inspect.signature(obj)
            print(f"  Signature: {sig}")
        except:
            pass

# Get the file path
print(f"\nfixit.rules module file: {fixit.rules.__file__}")

# List all available rules
import os
rules_dir = os.path.dirname(fixit.rules.__file__)
print(f"\nRules directory: {rules_dir}")
rule_files = [f for f in os.listdir(rules_dir) if f.endswith('.py') and not f.startswith('_')]
print(f"Rule files: {rule_files}")