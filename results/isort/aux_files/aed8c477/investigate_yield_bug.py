import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.identify import imports
from isort.settings import DEFAULT_CONFIG

# Test different yield scenarios
test_cases = [
    # Case 1: Simple yield with import after
    ("""
yield
import os
""", "os"),

    # Case 2: Import in function with yield
    ("""
def generator():
    yield
    import os
    return os
""", "os"),

    # Case 3: Yield from
    ("""
yield from something
import os
""", "os"),

    # Case 4: Yield in expression
    ("""
x = yield
import os  
""", "os"),

    # Case 5: Just yield keyword alone
    ("""
yield
import sys
""", "sys"),
]

print("Testing yield behavior in isort.identify.imports():\n")

for i, (code, expected_module) in enumerate(test_cases, 1):
    print(f"Test case {i}:")
    print(f"Code: {code.strip()}")
    
    stream = io.StringIO(code)
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    modules = [imp.module for imp in parsed_imports]
    print(f"Found imports: {modules}")
    
    if expected_module in modules:
        print(f"✓ Found expected module '{expected_module}'")
    else:
        print(f"✗ Missing expected module '{expected_module}'")
    
    print("-" * 50)

# Let's also test what happens with the specific lines
print("\nDetailed analysis of 'yield' handling:")

code = """import first
yield
import second
"""

stream = io.StringIO(code)
parsed = list(imports(stream, config=DEFAULT_CONFIG))

print(f"Input code:\n{code}")
print(f"Parsed imports: {[imp.module for imp in parsed]}")

# Try to understand the exact behavior
print("\nLet's trace through the code manually:")
code_lines = [
    "import first",
    "yield",  
    "import second"
]

for line_no, line in enumerate(code_lines, 1):
    print(f"Line {line_no}: '{line}'")
    stripped = line.strip().split("#")[0]
    print(f"  Stripped: '{stripped}'")
    if stripped.startswith(("raise", "yield")):
        print(f"  -> Would trigger special handling (lines 64-80)")
        if stripped == "yield":
            print(f"  -> Is bare 'yield', enters while loop to consume lines")
    elif line.strip().startswith(("import ", "from ")):
        print(f"  -> Is an import statement")