# Bug Report: Cython.Plex chars_to_ranges Incorrectly Handles Duplicate Characters

**Target**: `Cython.Plex.Regexps.chars_to_ranges`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `chars_to_ranges` function incorrectly expands character ranges when given duplicate characters, causing `Any()` regex patterns to incorrectly match newline characters.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from Cython.Plex.Regexps import Any
import string

@given(st.text(alphabet=string.printable, min_size=1, max_size=20))
def test_any_anybut_complement(chars):
    any_re = Any(chars)
    
    # AnyBut can match newline, Any cannot (unless newline is in chars)
    if '\n' not in chars:
        assert any_re.match_nl == 0
```

**Failing input**: `chars='\t\t'`

## Reproducing the Bug

```python
from Cython.Plex.Regexps import Any, chars_to_ranges

# Bug: Any() with duplicate tabs incorrectly matches newlines
chars = '\t\t'
any_re = Any(chars)

print(f"Any('{repr(chars)}').match_nl = {any_re.match_nl}")
print(f"Expected: 0 (tabs are not newlines)")

# Root cause: chars_to_ranges incorrectly merges duplicates
ranges = chars_to_ranges('\t\t')
print(f"chars_to_ranges('\\t\\t') = {ranges}")
print(f"Creates range [9, 11) which includes newline (10)")

# Real impact: Scanner incorrectly matches newlines
from Cython.Plex import Lexicon, Scanner, TEXT
from io import StringIO

lexicon = Lexicon([(Any('\t\t'), TEXT)])
scanner = Scanner(lexicon, StringIO('\n'))
result = scanner.read()
print(f"Scanner matches newline: {result} (should fail)")
```

## Why This Is A Bug

The `chars_to_ranges` function is supposed to convert a string of characters into a list of non-overlapping ranges. However, when given duplicate characters, it incorrectly extends the range beyond what it should.

For input `'\t\t'` (two tabs, both with code 9), the algorithm:
1. Starts with code1=9, code2=10 for the first tab
2. Sees the second tab (also 9) and since 10 >= 9, increments code2 to 11
3. Returns range [9, 11) which incorrectly includes newline (10)

This violates the documented behavior that `Any(s)` should only match characters in string `s`.

## Fix

```diff
--- a/Cython/Plex/Regexps.py
+++ b/Cython/Plex/Regexps.py
@@ -41,7 +41,9 @@ def chars_to_ranges(s):
         code2 = code1 + 1
         i += 1
         while i < n and code2 >= ord(char_list[i]):
-            code2 += 1
+            # Only increment code2 if we see a NEW character in sequence
+            if ord(char_list[i]) >= code2:
+                code2 = ord(char_list[i]) + 1
             i += 1
         result.append(code1)
         result.append(code2)
```