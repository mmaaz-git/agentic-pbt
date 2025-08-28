# Bug Report: isort.format Round-Trip Failure Changes Import Semantics

**Target**: `isort.format.format_natural` and `isort.format.format_simplified`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Round-tripping an import statement through `format_simplified()` and `format_natural()` changes its semantic meaning. `import a.b` becomes `from a import b`, which are different import statements in Python.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from isort.format import format_natural, format_simplified

@given(
    st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
        min_size=2,
        max_size=4
    )
)
def test_dotted_import_round_trip(parts):
    dotted = ".".join(parts)
    import_line = f"import {dotted}"
    
    simplified = format_simplified(import_line)
    restored = format_natural(simplified)
    
    # Should preserve the semantic meaning
    assert restored == import_line or restored.endswith(f"import {dotted}")
```

**Failing input**: `["a", "a"]` resulting in `"import a.a"`

## Reproducing the Bug

```python
from isort.format import format_natural, format_simplified

import_line = "import a.a"
simplified = format_simplified(import_line)
restored = format_natural(simplified)

print(f"Original: {import_line}")
print(f"Simplified: {simplified}")
print(f"Restored: {restored}")

assert restored == import_line, f"Semantic changed: '{import_line}' became '{restored}'"
```

## Why This Is A Bug

In Python, `import a.b` and `from a import b` have different semantics:
- `import a.b` imports the module `a.b` and binds it to the name `a`
- `from a import b` imports `b` from module `a` and binds it to the name `b`

These are fundamentally different operations that affect namespace and available symbols differently. A formatting tool should never change the semantic meaning of code.

## Fix

The issue is in `format_natural()` which incorrectly assumes all dotted paths should become `from X import Y` statements. It needs to track whether the original was an `import` or `from` statement:

```diff
--- a/isort/format.py
+++ b/isort/format.py
@@ -33,8 +33,12 @@ def format_natural(import_line: str) -> str:
     if not import_line.startswith("from ") and not import_line.startswith("import "):
         if "." not in import_line:
             return f"import {import_line}"
-        parts = import_line.split(".")
-        end = parts.pop(-1)
-        return f"from {'.'.join(parts)} import {end}"
+        # Check if this should remain as "import a.b.c" 
+        # rather than converting to "from a.b import c"
+        # This requires additional context about the original import type
+        # For now, default to import for dotted paths
+        return f"import {import_line}"
 
     return import_line
```