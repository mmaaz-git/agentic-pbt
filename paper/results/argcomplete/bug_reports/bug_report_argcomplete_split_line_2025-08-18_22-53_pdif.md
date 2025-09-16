# Bug Report: argcomplete.split_line Crashes with Unclosed Quote and Point Beyond String Length

**Target**: `argcomplete.split_line`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `split_line` function crashes with an ArgcompleteException when given an unclosed quote character and a point parameter that exceeds the string length.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from argcomplete import split_line

@given(st.text(), st.integers(min_value=0, max_value=200))
def test_split_line_with_point_returns_5_tuple(line, point):
    """split_line with point should always return a 5-tuple"""
    point = min(point, len(line) + 1)
    result = split_line(line, point)
    assert isinstance(result, tuple)
    assert len(result) == 5
```

**Failing input**: `line='"', point=2`

## Reproducing the Bug

```python
from argcomplete import split_line

line = '"'
point = 2
result = split_line(line, point)
```

## Why This Is A Bug

The function raises an ArgcompleteException with the message "Unexpected internal state. Please report this bug at https://github.com/kislyuk/argcomplete/issues." This indicates the developers consider this scenario a bug. The function should handle this edge case gracefully rather than crashing, especially since unclosed quotes can occur during interactive typing when tab completion is invoked mid-quote.

## Fix

The issue occurs because when point > len(line), the line is not truncated but the lexer still tries to read beyond the available input. The fix involves checking the bounds properly:

```diff
--- a/argcomplete/lexers.py
+++ b/argcomplete/lexers.py
@@ -5,7 +5,7 @@
 def split_line(line, point=None):
     if point is None:
         point = len(line)
-    line = line[:point]
+    line = line[:min(point, len(line))]
     lexer = _shlex.shlex(line, posix=True)
     lexer.whitespace_split = True
```