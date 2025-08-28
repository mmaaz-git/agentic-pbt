#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

import win32ctypes.core
import inspect
import os

# List the redirected modules
redirected_modules = [
    '_dll', '_authentication', '_time',
    '_common', '_resource', '_nl_support',
    '_system_information'
]

# Check which backend is being used
backend = win32ctypes.core._backend
print(f"Backend: {backend}")

# Import and inspect each module
for module_name in redirected_modules:
    try:
        module = __import__(f'win32ctypes.core.{module_name}', fromlist=[module_name])
        print(f"\n=== Module: win32ctypes.core.{module_name} ===")
        print(f"File: {module.__file__}")
        
        # Get all functions and classes
        functions = []
        classes = []
        for name, obj in inspect.getmembers(module):
            if not name.startswith('_'):
                if inspect.isfunction(obj):
                    functions.append(name)
                elif inspect.isclass(obj):
                    classes.append(name)
        
        if functions:
            print(f"Functions: {', '.join(functions)}")
        if classes:
            print(f"Classes: {', '.join(classes)}")
            
    except Exception as e:
        print(f"\nError importing win32ctypes.core.{module_name}: {e}")