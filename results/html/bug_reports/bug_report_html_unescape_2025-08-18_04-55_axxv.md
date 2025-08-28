# Bug Report: html.unescape Incorrectly Handles Control Characters

**Target**: `html.unescape`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `html.unescape()` function incorrectly returns empty strings for certain control character references (codepoints 1-8, 11, 14-31) instead of converting them to the corresponding Unicode characters as specified by the HTML5 standard.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import html

@given(st.integers(1, 31))
def test_control_char_unescaping(codepoint):
    """Test that control character references are properly unescaped"""
    dec_ref = f"&#{codepoint};"
    hex_ref = f"&#x{codepoint:x};"
    
    dec_result = html.unescape(dec_ref)
    hex_result = html.unescape(hex_ref)
    expected = chr(codepoint)
    
    # Both forms should produce the same result
    assert dec_result == hex_result
    
    # Valid control characters should be unescaped to the character
    # (even though they are parse errors per HTML5)
    if codepoint not in [0]:  # 0 is special-cased to replacement character
        assert dec_result == expected
```

**Failing input**: `codepoint=1`

## Reproducing the Bug

```python
import html

ref = "&#1;"
result = html.unescape(ref)
expected = chr(1)

print(f"Input: {repr(ref)}")
print(f"Output: {repr(result)}")
print(f"Expected: {repr(expected)}")

assert result == expected
```

## Why This Is A Bug

According to the HTML5 specification (section 13.2.5.70 "Numeric character reference end state"), control characters in the ranges U+0001 to U+0008, U+000E to U+001F, U+007F to U+009F, etc. are parse errors but should still result in the corresponding Unicode character being returned. The current implementation incorrectly returns empty strings for many of these codepoints.

The bug is in `/lib/python3.13/html/__init__.py` lines 103-104, where codepoints in the `_invalid_codepoints` set return empty strings instead of the actual characters.

## Fix

```diff
--- a/html/__init__.py
+++ b/html/__init__.py
@@ -100,8 +100,6 @@ def _replace_charref(s):
             return _invalid_charrefs[num]
         if 0xD800 <= num <= 0xDFFF or num > 0x10FFFF:
             return '\uFFFD'
-        if num in _invalid_codepoints:
-            return ''
         return chr(num)
     else:
         # named charref
```

Alternatively, if the intent is to follow the HTML5 standard more closely where these are parse errors, the function should at least be consistent and properly document this deviation from the standard.