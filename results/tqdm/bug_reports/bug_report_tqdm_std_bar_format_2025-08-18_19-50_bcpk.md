# Bug Report: tqdm.std.Bar ValueError on Non-Numeric Format Specifiers

**Target**: `tqdm.std.Bar.__format__`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The Bar class's `__format__` method crashes with ValueError when given format specifiers containing non-numeric characters that are not recognized type indicators ('a', 'u', 'b').

## Property-Based Test

```python
from hypothesis import given, strategies as st
from tqdm.std import Bar

@given(
    frac=st.floats(min_value=0, max_value=1, allow_nan=False),
    default_len=st.integers(min_value=1, max_value=50),
    format_spec=st.text(min_size=0, max_size=3)
)
def test_bar_format_robustness(frac, default_len, format_spec):
    bar = Bar(frac, default_len=default_len)
    try:
        output = format(bar, format_spec)
        assert isinstance(output, str)
    except ValueError:
        assert False, f"Bar.__format__ should handle format_spec={repr(format_spec)} gracefully"
```

**Failing input**: `frac=0.5, default_len=10, format_spec='²'`

## Reproducing the Bug

```python
from tqdm.std import Bar

bar = Bar(0.5, default_len=10)
output = format(bar, '²')  # ValueError: invalid literal for int() with base 10: '²'
```

## Why This Is A Bug

The Bar class documentation states it accepts format specifiers with `[width][type]` syntax. However, when an invalid format specifier is provided, the method attempts to parse it as an integer without proper error handling, causing an unhandled ValueError. The code should either handle invalid format specs gracefully or provide a clear error message.

## Fix

```diff
--- a/tqdm/std.py
+++ b/tqdm/std.py
@@ -193,7 +193,11 @@ class Bar(object):
             else:
                 format_spec = format_spec[:-1]
             if format_spec:
-                N_BARS = int(format_spec)
+                try:
+                    N_BARS = int(format_spec)
+                except ValueError:
+                    # Invalid format spec, use default
+                    N_BARS = self.default_len
                 if N_BARS < 0:
                     N_BARS += self.default_len
             else: