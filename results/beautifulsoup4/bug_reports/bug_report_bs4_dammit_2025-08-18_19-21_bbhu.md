# Bug Report: bs4.dammit Encoding Misdetection for Short Byte Sequences

**Target**: `bs4.dammit.UnicodeDammit`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

UnicodeDammit incorrectly detects the encoding of short byte sequences like `b'^'` as cp037 (EBCDIC) instead of ASCII/UTF-8, causing the character '^' to be decoded as ';'.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import bs4.dammit

@given(st.binary(min_size=1, max_size=1000))
def test_unicode_dammit_preserves_valid_utf8(data):
    """Test that UnicodeDammit correctly decodes valid UTF-8 data."""
    try:
        expected = data.decode('utf-8')
    except UnicodeDecodeError:
        return  # Skip non-UTF-8 data
    
    ud = bs4.dammit.UnicodeDammit(data)
    assert ud.unicode_markup == expected
```

**Failing input**: `b'^'`

## Reproducing the Bug

```python
import bs4.dammit
import bs4

# Test with UnicodeDammit directly
data = b'^'
ud = bs4.dammit.UnicodeDammit(data)
print(f"Input: {data}")
print(f"Expected: '^'")
print(f"Actual: '{ud.unicode_markup}'")
print(f"Detected encoding: {ud.original_encoding}")

# Test with BeautifulSoup
soup = bs4.BeautifulSoup(b'^', 'html.parser')
print(f"BeautifulSoup result: '{soup.get_text()}'")

assert ud.unicode_markup == '^', f"Expected '^' but got '{ud.unicode_markup}'"
```

## Why This Is A Bug

This violates expected behavior because:
1. The byte `0x5E` is the standard ASCII/UTF-8 encoding for the '^' character
2. ASCII should be preferred over obscure EBCDIC encodings like cp037
3. Real-world usage: `BeautifulSoup(b'^', 'html.parser')` produces ';' instead of '^'
4. The charset_normalizer library is making poor encoding guesses for very short inputs

## Fix

The issue stems from charset_normalizer incorrectly guessing EBCDIC encodings for short byte sequences. A fix would involve either:
1. Setting a minimum byte length before consulting charset_normalizer
2. Prioritizing ASCII/UTF-8 for short sequences
3. Excluding EBCDIC encodings unless explicitly requested

```diff
# In bs4/dammit.py, EncodingDetector class
def encodings(self):
    # ... existing code ...
    
    # Don't use charset detection for very short inputs
+   if len(self.markup) < 10:
+       # For short inputs, skip charset detection and use default encodings
+       yield 'ascii'
+       yield 'utf-8'
+       yield 'windows-1252'
+       return
    
    # ... rest of existing charset detection code ...
```