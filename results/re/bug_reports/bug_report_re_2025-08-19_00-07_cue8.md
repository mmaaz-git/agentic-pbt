# Bug Report: re Module Undocumented Negative Parameter Behavior

**Target**: `re.split` and `re.sub` functions
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `re.split()` and `re.sub()` functions treat negative values for `maxsplit` and `count` parameters as "no operations", which is undocumented and contradicts the documentation for `split` that states "If maxsplit is nonzero, at most maxsplit splits occur".

## Property-Based Test

```python
from hypothesis import given, strategies as st
import re

@given(
    st.text(alphabet='01', min_size=1, max_size=5),
    st.integers(min_value=-100, max_value=-1)
)
def test_negative_maxsplit_should_allow_splits(pattern, maxsplit):
    """According to docs, nonzero maxsplit should allow splits."""
    string = '010101'
    result = re.split(pattern, string, maxsplit=maxsplit)
    # Since maxsplit is nonzero (negative), docs suggest splits should occur
    # But they don't - the string is returned unsplit
    assert result != [string], f"Negative maxsplit={maxsplit} prevented all splits"
```

**Failing input**: `pattern='0', maxsplit=-1`

## Reproducing the Bug

```python
import re

# Negative maxsplit prevents all splits (undocumented)
result = re.split(',', 'a,b,c', maxsplit=-1)
print(f"split with maxsplit=-1: {result}")
assert result == ['a,b,c']

# Contrast with maxsplit=0 (unlimited splits)
result = re.split(',', 'a,b,c', maxsplit=0)
print(f"split with maxsplit=0: {result}")
assert result == ['a', 'b', 'c']

# Similarly for re.sub with negative count
result = re.sub('a', 'X', 'aaa', count=-1)
print(f"sub with count=-1: {result}")
assert result == 'aaa'

result = re.sub('a', 'X', 'aaa', count=0)
print(f"sub with count=0: {result}")
assert result == 'XXX'
```

## Why This Is A Bug

The documentation for `re.split` states: "If maxsplit is nonzero, at most maxsplit splits occur". Since -1 is nonzero, this implies splits should occur, but they don't. The behavior where negative values prevent operations entirely is undocumented for both `split` and `sub`. This creates confusion as users might expect:
1. Negative values to work like unlimited (common convention)
2. Negative values to follow the "nonzero" rule stated in docs
3. At minimum, the behavior to be documented

## Fix

Update the documentation to clarify the behavior of negative values:

```diff
--- a/Modules/_sre/sre.c
+++ b/Modules/_sre/sre.c
@@ split(pattern, string, maxsplit=0, flags=0)
     Split the source string by the occurrences of the pattern,
     returning a list containing the resulting substrings.  If
     capturing parentheses are used in pattern, then the text of all
     groups in the pattern are also returned as part of the resulting
-    list.  If maxsplit is nonzero, at most maxsplit splits occur,
+    list.  If maxsplit is positive, at most maxsplit splits occur,
+    if maxsplit is zero or omitted, all possible splits are made,
+    and if maxsplit is negative, no splits occur,
     and the remainder of the string is returned as the final element
     of the list.

@@ sub(pattern, repl, string, count=0, flags=0)
     Return the string obtained by replacing the leftmost
     non-overlapping occurrences of the pattern in string by the
     replacement repl.  repl can be either a string or a callable;
     if a string, backslash escapes in it are processed.  If it is
     a callable, it's passed the Match object and must return
-    a replacement string to be used.
+    a replacement string to be used. If count is positive, at most
+    count replacements are made. If count is zero or omitted, all
+    occurrences are replaced. If count is negative, no replacements
+    are made.
```