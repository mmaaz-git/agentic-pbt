#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
from troposphere.validators import integer, boolean

print("=== integer validator ===")
print(f"Module: {integer.__module__}")
print(f"File: {inspect.getfile(integer)}")
print(f"Source:")
print(inspect.getsource(integer))

print("\n=== boolean validator ===")
print(f"Module: {boolean.__module__}")
print(f"File: {inspect.getfile(boolean)}")
print(f"Source:")
print(inspect.getsource(boolean))