#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from sudachipy import Config
import inspect

print("Testing Config class:")
print("=" * 60)

# Check Config class
print("Config class signature:")
print(inspect.signature(Config.__init__) if hasattr(Config, '__init__') else "No __init__")

# Try creating a Config
try:
    config = Config()
    print(f"Empty Config created: {config}")
    print(f"Type: {type(config)}")
    
    # Check attributes
    attrs = [a for a in dir(config) if not a.startswith('_')]
    print(f"Public attributes: {attrs}")
    
    # Try with path
    config_with_path = Config.parse("/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages/sudachipy/resources/sudachi.json")
    print(f"Config from file: {config_with_path}")
    
    # Try parsing string
    config_from_str = Config.parse('{"systemDict": "test"}')
    print(f"Config from string: {config_from_str}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Check PosMatcher
print("\n" + "=" * 60)
print("Checking other classes that might be testable:")

# Check errors module
try:
    from sudachipy import errors
    print(f"Errors module members: {[m for m in dir(errors) if not m.startswith('_')]}")
except ImportError as e:
    print(f"Could not import errors: {e}")