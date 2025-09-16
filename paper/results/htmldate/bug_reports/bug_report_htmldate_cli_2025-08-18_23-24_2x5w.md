# Bug Report: htmldate.cli parse_args Ignores Parameter

**Target**: `htmldate.cli.parse_args`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `parse_args` function ignores its `args` parameter and always parses `sys.argv` instead, causing unexpected behavior when called programmatically.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sys
from htmldate.cli import parse_args

@given(
    st.booleans(),  # fast
    st.one_of(st.none(), st.text(min_size=1)),  # inputfile
    st.booleans(),  # original
)
def test_parse_args_combinations(fast, inputfile, original):
    # Save original argv
    old_argv = sys.argv
    # Set problematic argv that would cause parse error
    sys.argv = ["test", "--invalid-argument"]
    
    args = []
    if not fast:
        args.append("--fast")
    if inputfile:
        args.extend(["-i", inputfile])
    if original:
        args.append("--original")
    
    try:
        parsed = parse_args(args)
        # Should succeed with provided args
        assert parsed.fast == fast
    finally:
        sys.argv = old_argv
```

**Failing input**: Any call to `parse_args` when `sys.argv` contains unexpected arguments

## Reproducing the Bug

```python
import sys
from htmldate.cli import parse_args

old_argv = sys.argv
sys.argv = ["pytest", "test_file.py", "--tb=short"]

try:
    args = parse_args([])  # Should parse empty list
except SystemExit:
    print("BUG: parse_args uses sys.argv instead of its parameter")
finally:
    sys.argv = old_argv
```

## Why This Is A Bug

The function accepts an `args` parameter but never uses it. Line 70 calls `argsparser.parse_args()` without passing the `args` parameter. This makes the function unusable in contexts where `sys.argv` contains unrelated arguments (e.g., test runners, notebooks, embedded usage).

## Fix

```diff
--- a/htmldate/cli.py
+++ b/htmldate/cli.py
@@ -67,7 +67,7 @@ def parse_args(args: Any) -> Any:
         action="version",
         version=f"Htmldate {__version__} - Python {python_version()}",
     )
-    return argsparser.parse_args()
+    return argsparser.parse_args(args)
 
 
 def process_args(args: Any) -> None:
```