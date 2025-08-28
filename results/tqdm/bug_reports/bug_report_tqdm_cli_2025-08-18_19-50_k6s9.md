# Bug Report: tqdm.cli.cast Backslash Escape Sequence Handling

**Target**: `tqdm.cli.cast`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `cast` function in tqdm.cli fails to correctly handle the escaped backslash sequence `\\` when casting to 'chr' type, raising a TqdmTypeError instead of returning the expected single backslash byte.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tqdm.cli
from tqdm.cli import TqdmTypeError

@given(st.sampled_from(['\\\\', '\\\\\\\\', '\\\\n', '\\\\t']))
def test_cast_chr_backslash_sequences(escape):
    """Test that backslash escape sequences are handled correctly"""
    if escape == '\\\\':
        # This should work but currently fails
        result = tqdm.cli.cast(escape, 'chr')
        assert result == b'\\'
    else:
        # These compound sequences also fail
        try:
            result = tqdm.cli.cast(escape, 'chr')
        except TqdmTypeError:
            pass
```

**Failing input**: `'\\\\'` (representing the two-character string of two backslashes)

## Reproducing the Bug

```python
import tqdm.cli
from tqdm.cli import TqdmTypeError

# This should return b'\\' but raises TqdmTypeError
try:
    result = tqdm.cli.cast('\\\\', 'chr')
    print(f"Result: {result!r}")
except TqdmTypeError as e:
    print(f"Error: {e}")

# Show that Python's eval handles this correctly
correct_result = eval('"\\\\\"').encode()
print(f"Expected: {correct_result!r}")
```

## Why This Is A Bug

The `cast` function uses `eval(f'"{val}"')` to evaluate escape sequences, but only when the input matches the regex pattern `^\\\w+$`. This pattern requires a backslash followed by word characters (letters, digits, underscore). Since a backslash is not a word character, the valid escape sequence `\\` (escaped backslash) doesn't match the pattern and incorrectly raises an error. This violates the expected behavior that standard Python escape sequences should be handled correctly.

## Fix

```diff
--- a/tqdm/cli.py
+++ b/tqdm/cli.py
@@ -34,7 +34,7 @@ def cast(val, typ):
     if typ == 'chr':
         if len(val) == 1:
             return val.encode()
-        if re.match(r"^\\\w+$", val):
+        if re.match(r"^\\(.|\w)+$", val):
             return eval(f'"{val}"').encode()
         raise TqdmTypeError(f"{val} : {typ}")
     if typ == 'str':
```

Alternative fix using a more comprehensive pattern:
```diff
--- a/tqdm/cli.py
+++ b/tqdm/cli.py
@@ -34,7 +34,7 @@ def cast(val, typ):
     if typ == 'chr':
         if len(val) == 1:
             return val.encode()
-        if re.match(r"^\\\w+$", val):
+        if val.startswith('\\') and len(val) >= 2:
             return eval(f'"{val}"').encode()
         raise TqdmTypeError(f"{val} : {typ}")
     if typ == 'str':
```