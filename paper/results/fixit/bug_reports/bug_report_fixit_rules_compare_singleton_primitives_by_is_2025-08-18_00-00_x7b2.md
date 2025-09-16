# Bug Report: fixit.rules.compare_singleton_primitives_by_is Crashes on Code Without Spaces

**Target**: `fixit.rules.compare_singleton_primitives_by_is.CompareSingletonPrimitivesByIs`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The CompareSingletonPrimitivesByIs rule crashes with a CSTValidationError when processing comparisons that don't have spaces around the operator (e.g., `x==None`).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pathlib import Path
from fixit.engine import LintRunner
from fixit.ftypes import Config
from fixit.rules.compare_singleton_primitives_by_is import CompareSingletonPrimitivesByIs

@given(
    ws_before=st.sampled_from(['', ' ', '  ']),
    ws_after=st.sampled_from(['', ' ', '  ']),
    singleton=st.sampled_from(['None', 'True', 'False'])
)
def test_whitespace_handling(ws_before: str, ws_after: str, singleton: str):
    code = f"x{ws_before}=={ws_after}{singleton}"
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = CompareSingletonPrimitivesByIs()
    violations = list(runner.collect_violations([rule], config))
    assert len(violations) > 0  # Should detect the violation without crashing
```

**Failing input**: `x==None` (no spaces around ==)

## Reproducing the Bug

```python
from pathlib import Path
from fixit.engine import LintRunner
from fixit.ftypes import Config
from fixit.rules.compare_singleton_primitives_by_is import CompareSingletonPrimitivesByIs

code = "x==None"
path = Path.cwd() / "test.py"
config = Config(path=path)
runner = LintRunner(path, code.encode())
rule = CompareSingletonPrimitivesByIs()

try:
    violations = list(runner.collect_violations([rule], config))
    print(f"Got {len(violations)} violations")
except Exception as e:
    print(f"Crashed with: {type(e).__name__}: {e}")
```

## Why This Is A Bug

The rule should handle all valid Python code, including comparisons without spaces. Python allows `x==None` as valid syntax, so the lint rule should either:
1. Successfully apply the fix with appropriate spacing
2. Report the violation without attempting an invalid fix
3. Add spaces when creating the replacement

Instead, it crashes with `CSTValidationError: Must have at least one space around comparison operator.`

## Fix

```diff
--- a/fixit/rules/compare_singleton_primitives_by_is.py
+++ b/fixit/rules/compare_singleton_primitives_by_is.py
@@ -113,15 +113,26 @@ class CompareSingletonPrimitivesByIs(LintRule):
     def alter_operator(
         self, original_op: Union[cst.Equal, cst.NotEqual]
     ) -> Union[cst.Is, cst.IsNot]:
+        # Ensure we have at least one space around the operator
+        whitespace_before = original_op.whitespace_before
+        whitespace_after = original_op.whitespace_after
+        
+        # Add spaces if they're missing (LibCST requires spaces for Is/IsNot)
+        if not whitespace_before.value:
+            whitespace_before = cst.SimpleWhitespace(" ")
+        if not whitespace_after.value:
+            whitespace_after = cst.SimpleWhitespace(" ")
+        
         return (
             cst.IsNot(
-                whitespace_before=original_op.whitespace_before,
-                whitespace_after=original_op.whitespace_after,
+                whitespace_before=whitespace_before,
+                whitespace_between=cst.SimpleWhitespace(" "),
+                whitespace_after=whitespace_after,
             )
             if isinstance(original_op, cst.NotEqual)
             else cst.Is(
-                whitespace_before=original_op.whitespace_before,
-                whitespace_after=original_op.whitespace_after,
+                whitespace_before=whitespace_before,
+                whitespace_after=whitespace_after,
             )
         )
```