# Bug Report: isort.format.format_natural Returns Invalid Import for Empty String

**Target**: `isort.format.format_natural`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `format_natural()` function returns `"import "` when given an empty string input, instead of returning an empty string.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from isort.format import format_natural

@given(st.text(alphabet=" \t\n", min_size=0, max_size=10))
def test_format_natural_whitespace_only(whitespace):
    result = format_natural(whitespace)
    assert result == ""
```

**Failing input**: `""`

## Reproducing the Bug

```python
from isort.format import format_natural

result = format_natural("")
print(f"Result: '{result}'")
assert result == "", f"Expected empty string, got '{result}'"
```

## Why This Is A Bug

The function should handle empty strings gracefully. Returning `"import "` for an empty input creates invalid Python syntax and violates the principle that empty input should produce empty output for a formatting function.

## Fix

```diff
--- a/isort/format.py
+++ b/isort/format.py
@@ -31,6 +31,8 @@
 def format_natural(import_line: str) -> str:
     import_line = import_line.strip()
+    if not import_line:
+        return ""
     if not import_line.startswith("from ") and not import_line.startswith("import "):
         if "." not in import_line:
             return f"import {import_line}"
```