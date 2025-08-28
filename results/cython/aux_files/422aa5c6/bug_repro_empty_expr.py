import Cython.Tempita

# BUG: Empty expression causes SyntaxError
try:
    template = Cython.Tempita.Template('{{}}')
    result = template.substitute()
    print(f"Result: {repr(result)}")
except SyntaxError as e:
    print(f"Empty expression causes SyntaxError: {e}")

# This should probably either:
# 1. Return empty string '' (like None does)
# 2. Raise a more specific error about empty expressions
# 3. Be treated as literal text

# Compare with spaces-only expression
try:
    template2 = Cython.Tempita.Template('{{   }}')
    result2 = template2.substitute()
    print(f"Spaces-only result: {repr(result2)}")
except Exception as e:
    print(f"Spaces-only error: {e}")