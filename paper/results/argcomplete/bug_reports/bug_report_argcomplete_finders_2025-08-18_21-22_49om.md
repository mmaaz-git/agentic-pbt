# Bug Report: argcomplete.finders IndexError in quote_completions

**Target**: `argcomplete.finders.CompletionFinder.quote_completions`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `quote_completions` method crashes with `IndexError: string index out of range` when the wordbreak position causes a completion to be trimmed to an empty string.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from argcomplete.finders import CompletionFinder

@given(
    completion=st.text(alphabet="abc:def=ghi@jkl", min_size=5, max_size=20),
    wordbreak_pos=st.integers(min_value=-10, max_value=30)
)
def test_quote_completions_wordbreak_edge_cases(completion, wordbreak_pos):
    finder = CompletionFinder()
    result = finder.quote_completions([completion], "", wordbreak_pos)
    assert len(result) == 1
```

**Failing input**: `completion=':::::' wordbreak_pos=4`

## Reproducing the Bug

```python
from argcomplete.finders import CompletionFinder

finder = CompletionFinder()
completion = ":"
wordbreak_pos = 0

result = finder.quote_completions([completion], "", wordbreak_pos)
```

## Why This Is A Bug

When `last_wordbreak_pos` is not None, the method trims completions using `c[last_wordbreak_pos + 1:]`. If `last_wordbreak_pos + 1` equals the length of the completion string, this results in an empty string. The code then attempts to access the last character of this empty string at line 557 (`escaped_completions[0][-1]`), causing an IndexError.

This bug occurs in real-world scenarios when bash completion encounters wordbreak characters (like colons in option:value pairs) where the completion is exactly at the wordbreak position.

## Fix

```diff
--- a/argcomplete/finders.py
+++ b/argcomplete/finders.py
@@ -554,7 +554,7 @@ class CompletionFinder(object):
             # Now it is conditionally disabled using "compopt -o nospace" if the match ends in a continuation character.
             # This code is retained for environments where this isn't done natively.
             continuation_chars = "=/:"
-            if len(escaped_completions) == 1 and escaped_completions[0][-1] not in continuation_chars:
+            if len(escaped_completions) == 1 and escaped_completions[0] and escaped_completions[0][-1] not in continuation_chars:
                 if cword_prequote == "":
                     escaped_completions[0] += " "
```