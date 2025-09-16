#!/usr/bin/env python3
import sys
import inspect

print(f"Python version: {sys.version}")
print(f"Python version info: {sys.version_info}")

# Check if getargspec exists
if hasattr(inspect, 'getargspec'):
    print("inspect.getargspec exists")
else:
    print("inspect.getargspec does NOT exist")
    
# Check alternatives
if hasattr(inspect, 'getfullargspec'):
    print("inspect.getfullargspec exists (recommended replacement)")
    
if hasattr(inspect, 'signature'):
    print("inspect.signature exists (modern replacement)")