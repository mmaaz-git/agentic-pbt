#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/testpath_env/lib/python3.13/site-packages')

import testpath.tempdir
import inspect

print("Classes and functions in testpath.tempdir:")
members = inspect.getmembers(testpath.tempdir)
for name, obj in members:
    if inspect.isclass(obj):
        print(f"  Class: {name}")
        print(f"    Docstring: {obj.__doc__[:100] if obj.__doc__ else 'None'}...")
        print(f"    Methods: {[m for m in dir(obj) if not m.startswith('_')]}")
    elif inspect.isfunction(obj):
        print(f"  Function: {name}")
        print(f"    Signature: {inspect.signature(obj)}")

print("\nInspecting NamedFileInTemporaryDirectory:")
nf = testpath.tempdir.NamedFileInTemporaryDirectory
print(f"  __init__ signature: {inspect.signature(nf.__init__)}")
print(f"  Source file: {inspect.getfile(nf)}")

print("\nInspecting TemporaryWorkingDirectory:")
twd = testpath.tempdir.TemporaryWorkingDirectory
print(f"  __init__ signature: {inspect.signature(twd.__init__)}")
print(f"  Parent class: {twd.__bases__}")
print(f"  Source file: {inspect.getfile(twd)}")