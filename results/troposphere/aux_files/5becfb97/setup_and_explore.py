#!/usr/bin/env python3
import subprocess
import sys
import os

venv_python = "./venv/bin/python"

# Install packages
print("Installing packages...")
subprocess.run([venv_python, "-m", "pip", "install", "troposphere", "hypothesis", "pytest"], check=True)

# Explore troposphere.lakeformation
print("\nExploring troposphere.lakeformation...")
subprocess.run([venv_python, "-c", """
import troposphere.lakeformation
import inspect
import os

print(f"Module file: {troposphere.lakeformation.__file__}")
print(f"Module directory: {os.path.dirname(troposphere.lakeformation.__file__)}")

# Get all members
members = inspect.getmembers(troposphere.lakeformation)
print(f"\\nModule contains {len(members)} members")

# Filter for classes and functions
classes = [(name, obj) for name, obj in members if inspect.isclass(obj) and not name.startswith('_')]
functions = [(name, obj) for name, obj in members if inspect.isfunction(obj) and not name.startswith('_')]

print(f"\\nClasses ({len(classes)}):")
for name, _ in classes[:10]:  # Show first 10
    print(f"  - {name}")
if len(classes) > 10:
    print(f"  ... and {len(classes) - 10} more")

print(f"\\nFunctions ({len(functions)}):")
for name, _ in functions[:10]:  # Show first 10
    print(f"  - {name}")
if len(functions) > 10:
    print(f"  ... and {len(functions) - 10} more")
"""])