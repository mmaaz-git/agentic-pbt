import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from jurigged.utils import shift_lineno

# Create a simple code object
code_str = """
def test():
    pass
"""
code_obj = compile(code_str, "test.py", "exec")

print(f"Original line number: {code_obj.co_firstlineno}")

# This crashes with ValueError
try:
    shifted = shift_lineno(code_obj, -2)
    print(f"Successfully shifted to: {shifted.co_firstlineno}")
except ValueError as e:
    print(f"Error: {e}")
    print("Bug: shift_lineno doesn't handle negative line numbers")