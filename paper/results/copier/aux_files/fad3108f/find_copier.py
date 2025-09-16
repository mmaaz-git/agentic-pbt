#!/usr/bin/env python3
import sys
import os

# Add the venv site-packages to path
venv_path = '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages'
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)
    print(f"Added {venv_path} to sys.path")

# Now try to import copier
try:
    import copier
    print(f"Successfully imported copier from: {copier.__file__}")
    
    # Try to import copier.vcs
    import copier.vcs
    print(f"Successfully imported copier.vcs from: {copier.vcs.__file__}")
except ImportError as e:
    print(f"Failed to import copier: {e}")
    
# List what's in the venv site-packages
if os.path.exists(venv_path):
    print(f"\nContents of {venv_path}:")
    try:
        items = os.listdir(venv_path)
        for item in sorted(items):
            if 'copier' in item.lower():
                print(f"  - {item}")
    except Exception as e:
        print(f"Error listing directory: {e}")