#!/usr/bin/env python3

import inspect
import flask.blueprints

# Get module file location
print("Module file:", flask.blueprints.__file__)

# Get public members
public_members = [name for name, obj in inspect.getmembers(flask.blueprints) 
                  if not name.startswith('_')]
print("\nPublic members:", public_members)

# Analyze Blueprint class
Blueprint = flask.blueprints.Blueprint
print("\n\nBlueprint class signature:", inspect.signature(Blueprint))
print("\nBlueprint docstring:", Blueprint.__doc__[:500] if Blueprint.__doc__ else "No docstring")

# Check key methods
for method_name in ['register', 'route', 'add_url_rule', 'before_request', 'after_request']:
    if hasattr(Blueprint, method_name):
        method = getattr(Blueprint, method_name)
        print(f"\n{method_name} signature:", inspect.signature(method))

# Check BlueprintSetupState
if hasattr(flask.blueprints, 'BlueprintSetupState'):
    BSS = flask.blueprints.BlueprintSetupState
    print("\n\nBlueprintSetupState signature:", inspect.signature(BSS))
    print("BlueprintSetupState methods:", [m for m in dir(BSS) if not m.startswith('_')])