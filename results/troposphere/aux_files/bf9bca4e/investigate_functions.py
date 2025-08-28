#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import ast
import inspect
from jurigged import codetools

# Let's investigate specific functions that look testable

print("=== SPLITLINES FUNCTION ===")
print(f"Signature: {inspect.signature(codetools.splitlines)}")
print("Source:")
print(inspect.getsource(codetools.splitlines))

print("\n=== SUBSTANTIAL FUNCTION ===")
print(f"Signature: {inspect.signature(codetools.substantial)}")
print("Source:")
print(inspect.getsource(codetools.substantial))

print("\n=== ANALYZE_SPLIT FUNCTION ===")
print(f"Signature: {inspect.signature(codetools.analyze_split)}")
print("Source:")
print(inspect.getsource(codetools.analyze_split))

print("\n=== DELTA FUNCTION ===")
print(f"Signature: {inspect.signature(codetools.delta)}")
print("Source:")
print(inspect.getsource(codetools.delta))

print("\n=== DISTRIBUTE FUNCTION ===")
print(f"Signature: {inspect.signature(codetools.distribute)}")
try:
    print("Source:")
    print(inspect.getsource(codetools.distribute))
except:
    print("Could not get source")

print("\n=== Info class get_segment method ===")
try:
    print(inspect.getsource(codetools.Info.get_segment))
except:
    print("Could not get source")

print("\n=== Correspondence fitness method ===")
try:
    print(inspect.getsource(codetools.Correspondence.fitness))
except:
    print("Could not get source")