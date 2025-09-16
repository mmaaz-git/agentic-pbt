#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere

# Get the base classes
print("AWSObject source file:", inspect.getfile(troposphere.AWSObject))
print("AWSProperty source file:", inspect.getfile(troposphere.AWSProperty))

# Get signatures and docstrings
print("\n=== AWSObject ===")
print("Docstring:", troposphere.AWSObject.__doc__)
print("Methods:", [name for name, _ in inspect.getmembers(troposphere.AWSObject) if not name.startswith('_')])

print("\n=== AWSProperty ===")
print("Docstring:", troposphere.AWSProperty.__doc__)
print("Methods:", [name for name, _ in inspect.getmembers(troposphere.AWSProperty) if not name.startswith('_')])