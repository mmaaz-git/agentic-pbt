#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pywin32-ctypes_env/lib/python3.13/site-packages')

import inspect
import os

# Directly import the ctypes backend modules
backend_modules = [
    'win32ctypes.core.ctypes._dll',
    'win32ctypes.core.ctypes._authentication', 
    'win32ctypes.core.ctypes._time',
    'win32ctypes.core.ctypes._common',
    'win32ctypes.core.ctypes._resource',
    'win32ctypes.core.ctypes._nl_support',
    'win32ctypes.core.ctypes._system_information'
]

for module_path in backend_modules:
    try:
        module = __import__(module_path, fromlist=[module_path.split('.')[-1]])
        module_name = module_path.split('.')[-1]
        print(f"\n=== Module: {module_path} ===")
        print(f"File: {module.__file__}")
        
        # Get all functions and classes
        functions = []
        classes = []
        constants = []
        for name, obj in inspect.getmembers(module):
            if not name.startswith('_'):
                if inspect.isfunction(obj):
                    functions.append(name)
                elif inspect.isclass(obj):
                    classes.append(name)
                elif isinstance(obj, (int, str)):
                    constants.append(name)
        
        if functions:
            print(f"Functions: {', '.join(functions)}")
        if classes:
            print(f"Classes: {', '.join(classes)}")
        if constants and len(constants) < 10:  # Only show if not too many
            print(f"Constants: {', '.join(constants)}")
            
    except Exception as e:
        print(f"\nError importing {module_path}: {e}")