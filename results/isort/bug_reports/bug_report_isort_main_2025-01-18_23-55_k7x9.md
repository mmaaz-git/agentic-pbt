# Bug Report: isort.main Accepts Invalid Negative and Zero line_length Values

**Target**: `isort.main.parse_args` and `isort.settings.Config`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The `parse_args` function in isort.main accepts negative and zero values for `line_length` and `wrap_length` parameters, which are illogical for code formatting and can lead to unexpected behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import isort.main
from isort.settings import Config

@given(line_length=st.integers(min_value=-1000, max_value=0))
def test_invalid_line_length(line_length):
    # parse_args should reject negative/zero line_length
    result = isort.main.parse_args(["--line-length", str(line_length)])
    
    if line_length <= 0:
        # This should not be accepted
        assert result.get('line_length') != line_length, f"Accepted invalid line_length={line_length}"
        
        # Config should also reject it
        try:
            config = Config(line_length=line_length)
            assert False, f"Config accepted invalid line_length={line_length}"
        except ValueError:
            pass  # Expected
```

**Failing input**: `line_length=-10` or `line_length=0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.main
from isort.settings import Config

# Bug 1: Negative line_length is accepted
result = isort.main.parse_args(["--line-length", "-10"])
print(f"line_length = {result.get('line_length')}")  # Output: line_length = -10

# Bug 2: Zero line_length is accepted
result = isort.main.parse_args(["--line-length", "0"])
print(f"line_length = {result.get('line_length')}")  # Output: line_length = 0

# Bug 3: Negative wrap_length is accepted
result = isort.main.parse_args(["--wrap-length", "-5"])
print(f"wrap_length = {result.get('wrap_length')}")  # Output: wrap_length = -5

# These values can be passed to Config, potentially causing issues
config = Config(line_length=0)  # This succeeds but shouldn't
print(f"Config created with line_length={config.line_length}")
```

## Why This Is A Bug

1. **Negative line_length**: A negative line length makes no logical sense for code formatting. Lines cannot have negative lengths.

2. **Zero line_length**: A zero line length would mean no characters are allowed per line, which is impossible for any meaningful code formatting.

3. **Negative wrap_length**: Similar to line_length, negative wrap lengths are nonsensical.

4. **Inconsistency**: While Config validates that `wrap_length <= line_length`, it doesn't validate that these values are positive, leading to potential edge cases and unexpected behavior.

5. **User Experience**: Users who accidentally provide negative values (e.g., typos) won't get immediate feedback about their mistake.

## Fix

```diff
--- a/isort/main.py
+++ b/isort/main.py
@@ -649,7 +649,13 @@ def _build_arg_parser() -> argparse.ArgumentParser:
         "--line-width",
         help="The max length of an import line (used for wrapping long imports).",
         dest="line_length",
-        type=int,
+        type=lambda x: _validate_positive_int(x, "line_length"),
+    )
+
+def _validate_positive_int(value, name):
+    ivalue = int(value)
+    if ivalue <= 0:
+        raise argparse.ArgumentTypeError(f"{name} must be a positive integer, got {ivalue}")
+    return ivalue
     
     output_group.add_argument(
@@ -656,7 +662,7 @@ def _build_arg_parser() -> argparse.ArgumentParser:
         "--wrap-length",
         dest="wrap_length",
-        type=int,
+        type=lambda x: _validate_positive_int(x, "wrap_length"),
         help="Specifies how long lines that are wrapped should be, if not set line_length is used."
         "\nNOTE: wrap_length must be LOWER than or equal to line_length.",
     )

--- a/isort/settings.py
+++ b/isort/settings.py
@@ -278,6 +278,12 @@ class _Config:
             object.__setattr__(self, "lines_between_types", 1)
             object.__setattr__(self, "from_first", True)
+        if self.line_length <= 0:
+            raise ValueError(f"line_length must be positive, got {self.line_length}")
+            
+        if self.wrap_length < 0:
+            raise ValueError(f"wrap_length must be non-negative, got {self.wrap_length}")
+            
         if self.wrap_length > self.line_length:
             raise ValueError(
                 "wrap_length must be set lower than or equal to line_length: "
```