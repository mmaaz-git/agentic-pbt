#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from sudachipy import Config
import inspect

print("Investigating Config.update() method:")
print("=" * 60)

# Create a config
config = Config(projection='surface')
print(f"Initial config: {config}")
print(f"Initial projection: {config.projection}")

# Check the update method
print(f"\nConfig.update method: {config.update}")
print(f"Type: {type(config.update)}")

# Try to get signature
try:
    sig = inspect.signature(config.update)
    print(f"Signature: {sig}")
except Exception as e:
    print(f"Could not get signature: {e}")

# Check docstring
if hasattr(config.update, '__doc__'):
    print(f"\nDocstring: {config.update.__doc__}")

# Try different ways to call update
print("\n" + "=" * 60)
print("Testing different ways to call update:")

# Test 1: Try with dict argument (what we expected to work)
print("\n1. With dict argument:")
try:
    test_config = Config()
    test_config.update({'system': 'test'})
    print(f"  Success! Config after update: {test_config}")
except TypeError as e:
    print(f"  Failed: {e}")

# Test 2: Try with no arguments
print("\n2. With no arguments:")
try:
    test_config = Config()
    result = test_config.update()
    print(f"  Success! Result: {result}")
    print(f"  Config after: {test_config}")
except TypeError as e:
    print(f"  Failed: {e}")

# Test 3: Try with keyword arguments
print("\n3. With keyword arguments:")
try:
    test_config = Config()
    test_config.update(system='test', projection='normalized')
    print(f"  Success! Config after update: {test_config}")
except TypeError as e:
    print(f"  Failed: {e}")

# Test 4: Check if update might be a property
print("\n4. Check if update is a property or method:")
print(f"  Is method: {callable(config.update)}")
print(f"  Dir of update: {[d for d in dir(config.update) if not d.startswith('_')]}")

# Test 5: Try to understand what update actually does
print("\n5. Trying to understand update behavior:")
config1 = Config(projection='surface')
print(f"  Before update: {config1}")
try:
    # Maybe update() returns something?
    result = config1.update()
    print(f"  update() returned: {result}")
    print(f"  After update: {config1}")
except Exception as e:
    print(f"  Error: {e}")