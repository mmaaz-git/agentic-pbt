#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer, boolean, double
import inspect

# Find where validators are defined
print("=== Validator source ===")
print(f"integer source file: {inspect.getfile(integer)}")
print(f"boolean source file: {inspect.getfile(boolean)}")
print(f"double source file: {inspect.getfile(double)}")

print("\n=== Integer validator source ===")
print(inspect.getsource(integer))

print("\n=== Boolean validator source ===")
print(inspect.getsource(boolean))

print("\n=== Double validator source ===")
print(inspect.getsource(double))