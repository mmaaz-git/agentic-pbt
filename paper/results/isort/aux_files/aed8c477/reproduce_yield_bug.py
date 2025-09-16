#!/usr/bin/env python3
"""Minimal reproduction of the yield bug in isort.identify"""

import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.identify import imports
from isort.settings import DEFAULT_CONFIG

# Minimal test case
code = """import before_yield
yield
import after_yield
"""

print("Bug Reproduction: isort.identify skips imports after bare 'yield'\n")
print("Input code:")
print(code)

stream = io.StringIO(code)
parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))

print("\nExpected imports: ['before_yield', 'after_yield']")
print(f"Actual imports found: {[imp.module for imp in parsed_imports]}")

if 'after_yield' not in [imp.module for imp in parsed_imports]:
    print("\n❌ BUG CONFIRMED: Import 'after_yield' was not found!")
    print("The import statement after the bare 'yield' was incorrectly skipped.")
else:
    print("\n✓ No bug found")

# Additional test showing it works with non-bare yield
print("\n" + "="*60)
print("Control test with 'yield from' (should work correctly):")

code2 = """import before_yield
yield from something
import after_yield
"""

print(f"Input code:\n{code2}")

stream2 = io.StringIO(code2)
parsed_imports2 = list(imports(stream2, config=DEFAULT_CONFIG))

print(f"Imports found: {[imp.module for imp in parsed_imports2]}")

if 'after_yield' in [imp.module for imp in parsed_imports2]:
    print("✓ Works correctly with 'yield from'")

# Show why this is a problem
print("\n" + "="*60)
print("Why this is a bug:")
print("1. Valid Python code can have 'yield' statements followed by imports")
print("2. The parser is meant to find ALL imports in a file")  
print("3. Only bare 'yield' triggers this bug, not 'yield expr' or 'yield from'")
print("4. This could cause isort to miss organizing some imports in real code")