import sys
import types

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')
from jurigged.utils import shift_lineno

# Create a simple code object
code_str = """
def test_func():
    pass
"""

# Compile to get a code object with the function at line 2
compiled = compile(code_str, '<test>', 'exec')

# Find the nested function code object
for const in compiled.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'test_func':
        func_code = const
        break

print(f"Original function starts at line: {func_code.co_firstlineno}")

# Try to shift by -3 (which would make line number -1)
try:
    shifted = shift_lineno(func_code, -3)
    print(f"Shifted function starts at line: {shifted.co_firstlineno}")
except ValueError as e:
    print(f"Error occurred: {e}")
    print("Bug confirmed: shift_lineno doesn't handle negative line numbers")
    
# Additional test: what if we shift by exactly the negative of co_firstlineno?
try:
    shifted = shift_lineno(func_code, -func_code.co_firstlineno)
    print(f"Shifting by -{func_code.co_firstlineno} resulted in line: {shifted.co_firstlineno}")
except ValueError as e:
    print(f"Error with delta=-{func_code.co_firstlineno}: {e}")
    
# Test edge case: shift to exactly line 1
try:
    shifted = shift_lineno(func_code, 1 - func_code.co_firstlineno)
    print(f"Shifting to line 1 succeeded: {shifted.co_firstlineno}")
except ValueError as e:
    print(f"Error shifting to line 1: {e}")