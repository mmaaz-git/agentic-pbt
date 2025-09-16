import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.recode import make_recoder
from jurigged.register import registry
import inspect

# Check the registry.find function
print("registry.find signature:")
# registry.find is overloaded, let's see what it expects
print(type(registry.find))

# Check the implementation
print("\nmake_recoder source:")
print(inspect.getsource(make_recoder))

# Try with various invalid inputs to see what happens
test_inputs = [None, 42, "string", [], {}, 3.14]

print("\nTesting various inputs:")
for inp in test_inputs:
    try:
        result = make_recoder(inp)
        print(f"  make_recoder({repr(inp)}) = {result}")
    except Exception as e:
        print(f"  make_recoder({repr(inp)}) raised {e.__class__.__name__}: {e}")

# Check if there's documentation about what inputs are expected
print("\nmake_recoder docstring:", make_recoder.__doc__)

# Look for usage examples in the module
print("\nSearching for make_recoder usage in module...")
import jurigged
# List all modules in jurigged
import os
jurigged_path = os.path.dirname(jurigged.__file__)
print(f"Jurigged path: {jurigged_path}")