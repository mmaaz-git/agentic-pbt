#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import inspect
import importlib

# Key modules to explore
modules_to_explore = [
    'pyramid.url',
    'pyramid.util',
    'pyramid.encode', 
    'pyramid.path',
    'pyramid.settings',
    'pyramid.security',
    'pyramid.authentication',
    'pyramid.authorization',
    'pyramid.csrf',
    'pyramid.httpexceptions'
]

for module_name in modules_to_explore:
    print(f"\n{'='*60}")
    print(f"Module: {module_name}")
    print('='*60)
    
    try:
        mod = importlib.import_module(module_name)
        print(f"Location: {mod.__file__}")
        
        # Get public functions and classes
        members = inspect.getmembers(mod)
        functions = [(name, obj) for name, obj in members 
                    if inspect.isfunction(obj) and not name.startswith('_')]
        classes = [(name, obj) for name, obj in members 
                  if inspect.isclass(obj) and not name.startswith('_')]
        
        print(f"\nPublic Functions ({len(functions)}):")
        for name, func in functions[:5]:  # Show first 5
            try:
                sig = inspect.signature(func)
                print(f"  - {name}{sig}")
            except:
                print(f"  - {name}(...)")
        
        print(f"\nPublic Classes ({len(classes)}):")
        for name, cls in classes[:5]:
            print(f"  - {name}")
            
    except Exception as e:
        print(f"Error importing {module_name}: {e}")