# Bug Report: isort.identify Skips Imports After Bare 'yield' Statement

**Target**: `isort.identify.imports()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `imports()` function in isort.identify incorrectly skips import statements that appear after a bare `yield` keyword, causing isort to miss organizing those imports.

## Property-Based Test

```python
def test_import_after_yield():
    """Test that imports after yield statements are handled"""
    code = """
def generator():
    yield
    import os
    return os
"""
    stream = io.StringIO(code)
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    modules = [imp.module for imp in parsed_imports]
    assert "os" in modules  # This assertion fails
```

**Failing input**: Any code with a bare `yield` followed by an import statement

## Reproducing the Bug

```python
import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.identify import imports
from isort.settings import DEFAULT_CONFIG

code = """import before_yield
yield
import after_yield
"""

stream = io.StringIO(code)
parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))

print(f"Expected: ['before_yield', 'after_yield']")
print(f"Actual: {[imp.module for imp in parsed_imports]}")
```

## Why This Is A Bug

The parser is designed to find ALL imports in a Python file. When it encounters a bare `yield` statement, it enters a loop that consumes subsequent lines until finding a non-yield line, but then fails to process that consumed line for imports. This causes valid import statements to be missed, which could lead to isort failing to properly organize all imports in a file.

## Fix

The bug is in the `imports()` function in `/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages/isort/identify.py` at lines 64-80. When handling a bare `yield`, the code consumes lines but doesn't process the last consumed line.

```diff
--- a/isort/identify.py
+++ b/isort/identify.py
@@ -63,16 +63,22 @@ def imports(
         stripped_line = raw_line.strip().split("#")[0]
         if stripped_line.startswith(("raise", "yield")):
             if stripped_line == "yield":
+                last_consumed_line = None
+                last_consumed_index = index
                 while not stripped_line or stripped_line == "yield":
                     try:
                         index, next_line = next(indexed_input)
+                        last_consumed_line = next_line
+                        last_consumed_index = index
                     except StopIteration:
                         break
 
                     stripped_line = next_line.strip().split("#")[0]
+                # Process the last consumed line if it wasn't empty
+                if last_consumed_line and stripped_line and not stripped_line == "yield":
+                    # Put it back into processing by not continuing
+                    raw_line = last_consumed_line
+                    index = last_consumed_index
+                else:
+                    continue
             while stripped_line.endswith("\\"):
                 try:
                     index, next_line = next(indexed_input)
```

Note: A more elegant fix would be to restructure the logic to avoid consuming lines that need further processing, but the above patch illustrates the core issue.