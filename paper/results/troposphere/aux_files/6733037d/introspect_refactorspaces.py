#!/usr/bin/env python3
import troposphere.refactorspaces as refactorspaces
import inspect
import sys

# Get all classes and functions
classes = []
functions = []

for name, obj in inspect.getmembers(refactorspaces):
    if not name.startswith('_'):
        if inspect.isclass(obj):
            classes.append((name, obj))
        elif inspect.isfunction(obj):
            functions.append((name, obj))

print("=== CLASSES ===")
for name, cls in classes:
    print(f"\n{name}:")
    print(f"  Base classes: {[b.__name__ for b in cls.__bases__]}")
    
    # Get class docstring
    if cls.__doc__:
        print(f"  Docstring: {cls.__doc__[:200]}...")
    
    # Get methods
    methods = [m for m in dir(cls) if not m.startswith('_') and callable(getattr(cls, m))]
    if methods:
        print(f"  Public methods: {methods}")
    
    # Check if it has __init__
    if hasattr(cls, '__init__'):
        try:
            sig = inspect.signature(cls.__init__)
            print(f"  __init__ signature: {sig}")
        except:
            pass

print("\n=== FUNCTIONS ===")
for name, func in functions:
    print(f"\n{name}:")
    try:
        sig = inspect.signature(func)
        print(f"  Signature: {sig}")
    except:
        pass
    if func.__doc__:
        print(f"  Docstring: {func.__doc__[:200]}...")

# Check for specific properties that might be worth testing
print("\n=== MODULE ATTRIBUTES ===")
print(f"Module file: {refactorspaces.__file__}")
print(f"Module name: {refactorspaces.__name__}")

# Try to instantiate some classes with example data
print("\n=== INSTANTIATION EXAMPLES ===")
try:
    # Try Application
    app = refactorspaces.Application("TestApp")
    print(f"Application created: {app}")
    print(f"  Type: {type(app)}")
    print(f"  Dict representation: {app.to_dict()}")
except Exception as e:
    print(f"Failed to create Application: {e}")

try:
    # Try Environment
    env = refactorspaces.Environment("TestEnv")
    print(f"Environment created: {env}")
    print(f"  Type: {type(env)}")
    print(f"  Dict representation: {env.to_dict()}")
except Exception as e:
    print(f"Failed to create Environment: {e}")

try:
    # Try Service
    svc = refactorspaces.Service("TestService")
    print(f"Service created: {svc}")
    print(f"  Type: {type(svc)}")
    print(f"  Dict representation: {svc.to_dict()}")
except Exception as e:
    print(f"Failed to create Service: {e}")