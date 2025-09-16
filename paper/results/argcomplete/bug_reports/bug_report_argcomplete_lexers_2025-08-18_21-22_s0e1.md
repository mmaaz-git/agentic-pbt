# Bug Report: argcomplete.lexers Form Feed and Vertical Tab Not Treated as Whitespace

**Target**: `argcomplete.lexers.split_line`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `split_line` function incorrectly treats form feed (\x0c) and vertical tab (\x0b) characters as non-whitespace, returning them as words or prefix content instead of treating them as separators.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import argcomplete.lexers

@given(st.text(alphabet=' \t\n\r\f\v', min_size=1, max_size=50))
def test_only_whitespace_with_point(whitespace):
    """Test strings containing only various whitespace characters"""
    for point in [0, len(whitespace) // 2, len(whitespace)]:
        result = argcomplete.lexers.split_line(whitespace, point)
        prequote, prefix, suffix, words, wordbreak = result
        
        # For pure whitespace, should have empty results
        assert prefix == ''
        assert suffix == ''
        assert words == []
        assert prequote == ''
```

**Failing input**: `'\x0c'` (form feed) and `'\x0b'` (vertical tab)

## Reproducing the Bug

```python
import argcomplete.lexers

# Form feed character is not treated as whitespace
result = argcomplete.lexers.split_line('\x0c')
prequote, prefix, suffix, words, wordbreak = result
print(f"Form feed: prefix={repr(prefix)}, words={words}")
# Output: Form feed: prefix='\x0c', words=[]
# Expected: prefix='', words=[]

# Vertical tab has the same issue
result = argcomplete.lexers.split_line('\x0b')
prequote, prefix, suffix, words, wordbreak = result
print(f"Vertical tab: prefix={repr(prefix)}, words={words}")
# Output: Vertical tab: prefix='\x0b', words=[]
# Expected: prefix='', words=[]

# Compare with other whitespace that works correctly
result = argcomplete.lexers.split_line('\t')
prequote, prefix, suffix, words, wordbreak = result
print(f"Tab: prefix={repr(prefix)}, words={words}")
# Output: Tab: prefix='', words=[]
```

## Why This Is A Bug

While the underlying shlex module also doesn't treat \x0c and \x0b as whitespace by default, this creates inconsistent behavior in argcomplete's command-line parsing. Users would expect all standard whitespace characters to be treated uniformly as word separators. This could affect shell completion in terminals that use form feed or vertical tab characters.

## Fix

The issue stems from the shlex module's default whitespace definition. The fix would be to explicitly set the whitespace characters in the lexer to include form feed and vertical tab:

```diff
def split_line(line, point=None):
    if point is None:
        point = len(line)
    line = line[:point]
    lexer = _shlex.shlex(line, posix=True)
+   # Include all standard whitespace characters
+   lexer.whitespace = ' \t\r\n\f\v'
    lexer.whitespace_split = True
    lexer.wordbreaks = os.environ.get("_ARGCOMPLETE_COMP_WORDBREAKS", "")
```