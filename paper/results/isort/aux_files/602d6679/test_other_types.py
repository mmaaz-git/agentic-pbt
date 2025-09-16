import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import files
from isort.settings import Config

config = Config()

# Test with integers
print("Testing with integers...")
try:
    result = list(files.find([123, 456], config, [], []))
    print(f"  Result: {result}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test with floats
print("\nTesting with floats...")
try:
    result = list(files.find([3.14, 2.71], config, [], []))
    print(f"  Result: {result}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test with boolean
print("\nTesting with booleans...")
try:
    result = list(files.find([True, False], config, [], []))
    print(f"  Result: {result}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test with mixed types
print("\nTesting with mixed types...")
try:
    result = list(files.find(["file.py", None, 123, True], config, [], []))
    print(f"  Result: {result}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")