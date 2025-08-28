# Bug Report: fixit.engine Carriage Return Handling

**Target**: `fixit.engine.LintRunner`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

LintRunner fails to preserve carriage return (`\r`) characters when they appear standalone or as trailing whitespace, violating the idempotence property of apply_replacements.

## Property-Based Test

```python
@given(st.sampled_from(["\n", "\r\n", "\r", ""]))
def test_empty_and_whitespace_handling(whitespace):
    """
    Property: LintRunner should handle empty/whitespace files gracefully.
    Evidence: Real code often has trailing whitespace or empty files.
    """
    content = whitespace.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    # Should be able to apply empty replacements
    result = runner.apply_replacements([])
    assert isinstance(result, Module)
    assert result.code == whitespace  # FAILS for '\r'
```

**Failing input**: `'\r'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')
from fixit.engine import LintRunner
from pathlib import Path

# Bug 1: Standalone carriage return becomes empty string
content = b'\r'
runner = LintRunner(path=Path("test.py"), source=content)
result = runner.apply_replacements([])
print(f"Input: {repr(content.decode('utf-8'))}")  # '\r'
print(f"Output: {repr(result.code)}")             # ''
assert result.code == '\r'  # FAILS

# Bug 2: Trailing carriage return is removed
content = b'x = 1\r'
runner = LintRunner(path=Path("test.py"), source=content)
result = runner.apply_replacements([])
print(f"Input: {repr(content.decode('utf-8'))}")  # 'x = 1\r'
print(f"Output: {repr(result.code)}")             # 'x = 1'
assert result.code == 'x = 1\r'  # FAILS
```

## Why This Is A Bug

The `apply_replacements` method with an empty list should be idempotent - it should return a module with identical code to the input. However, carriage return characters are not preserved in two cases:

1. Standalone `\r` (empty file with just carriage return) becomes an empty string
2. Trailing `\r` after code is removed

This violates the expected behavior that whitespace and line endings should be preserved when no replacements are made. While `\r`-only line endings are rare in modern files, they are still valid and should be handled correctly.

## Fix

The bug originates in the underlying `libcst.parse_module` function which doesn't properly handle carriage returns. A workaround in fixit.engine could preserve the original source when no replacements are made:

```diff
--- a/fixit/engine.py
+++ b/fixit/engine.py
@@ -119,6 +119,10 @@ class LintRunner:
     def apply_replacements(self, violations: Collection[LintViolation]) -> Module:
         """
         Apply any autofixes to the module, and return the resulting source code.
         """
+        # If no replacements, return original module to preserve whitespace
+        if not violations:
+            return self.module
+            
         replacements = {v.node: v.replacement for v in violations if v.replacement}
 
         class ReplacementTransformer(CSTTransformer):
```

However, a proper fix would require addressing the issue in libcst's parse_module function to correctly preserve all whitespace characters including carriage returns.