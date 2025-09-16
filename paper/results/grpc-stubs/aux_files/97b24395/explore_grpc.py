#!/usr/bin/env python3
"""Explore the grpc module to understand available functionality."""

import sys
import os
import inspect

# Add the virtual environment to path
venv_path = '/root/hypothesis-llm/envs/grpc-stubs_env/lib/python3.13/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

import grpc

print("=== GRPC Module Analysis ===")
print(f"Location: {grpc.__file__}")
print(f"Version: {grpc.__version__ if hasattr(grpc, '__version__') else 'unknown'}")

print("\n=== Public Members ===")
members = inspect.getmembers(grpc)
classes = []
functions = []
constants = []

for name, obj in members:
    if not name.startswith('_'):
        if inspect.isclass(obj):
            classes.append((name, obj))
        elif inspect.isfunction(obj) or inspect.isbuiltin(obj):
            functions.append((name, obj))
        elif not inspect.ismodule(obj):
            constants.append((name, obj))

print(f"\nClasses ({len(classes)}):")
for name, cls in classes[:10]:  # Show first 10
    print(f"  - {name}")
    
print(f"\nFunctions ({len(functions)}):")
for name, func in functions[:10]:  # Show first 10
    print(f"  - {name}")

print(f"\nConstants ({len(constants)}):")
for name, const in constants[:10]:  # Show first 10
    print(f"  - {name}: {type(const).__name__}")

# Check for channelz-related functionality
print("\n=== Channelz-related items ===")
channelz_items = [name for name, _ in members if 'channelz' in name.lower()]
if channelz_items:
    for item in channelz_items:
        print(f"  - {item}")
else:
    print("  No channelz-related items found in main grpc module")

# Check submodules
print("\n=== Submodules ===")
import pkgutil
grpc_path = os.path.dirname(grpc.__file__)
for importer, modname, ispkg in pkgutil.iter_modules([grpc_path]):
    print(f"  - grpc.{modname} (package: {ispkg})")