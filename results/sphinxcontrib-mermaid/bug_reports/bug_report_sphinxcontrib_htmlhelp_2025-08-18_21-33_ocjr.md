# Bug Report: sphinxcontrib.htmlhelp C1 Control Characters Incorrectly Escaped

**Target**: `sphinxcontrib.htmlhelp.HTMLHelpBuilder._escape`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_escape` method incorrectly escapes C1 control characters (U+0080-U+009F) causing them to be transformed into different Unicode characters due to HTML's Windows-1252 legacy behavior.

## Property-Based Test

```python
import re
import html
import sphinxcontrib.htmlhelp as htmlhelp
from hypothesis import given, strategies as st

@given(st.text())
def test_escape_entire_string(text):
    """Test that escaping an entire string preserves the content."""
    builder = htmlhelp.HTMLHelpBuilder
    escaped = re.sub(r"[^\x00-\x7F]", builder._escape, text)
    unescaped = html.unescape(escaped)
    assert unescaped == text, f"Round-trip failed: {text!r} -> {escaped!r} -> {unescaped!r}"
```

**Failing input**: `'\x91'`

## Reproducing the Bug

```python
import re
import html
import sphinxcontrib.htmlhelp as htmlhelp

test_char = '\x91'
builder = htmlhelp.HTMLHelpBuilder
escaped = re.sub(r"[^\x00-\x7F]", builder._escape, test_char)
unescaped = html.unescape(escaped)

print(f"Original: U+{ord(test_char):04X}")
print(f"Escaped: {escaped}")
print(f"Unescaped: U+{ord(unescaped):04X}")
print(f"Characters match: {test_char == unescaped}")
```

## Why This Is A Bug

The `_escape` method converts non-ASCII characters to HTML numeric entities. However, HTML parsers interpret numeric references in the range &#128; to &#159; according to Windows-1252 encoding rather than Unicode. This causes 27 C1 control characters (U+0080-U+009F) to be silently transformed into different characters. For example, U+0091 becomes U+2018 (left single quotation mark).

## Fix

```diff
--- a/sphinxcontrib/htmlhelp/__init__.py
+++ b/sphinxcontrib/htmlhelp/__init__.py
@@ -189,11 +189,43 @@ class HTMLHelpBuilder(StandaloneHTMLBuilder):
         if body is not None:
             ctx["body"] = re.sub(r"[^\x00-\x7F]", self._escape, body)
 
+    # Windows-1252 mapping for problematic range
+    _WINDOWS_1252_MAP = {
+        0x80: 0x20AC, 0x82: 0x201A, 0x83: 0x0192, 0x84: 0x201E,
+        0x85: 0x2026, 0x86: 0x2020, 0x87: 0x2021, 0x88: 0x02C6,
+        0x89: 0x2030, 0x8A: 0x0160, 0x8B: 0x2039, 0x8C: 0x0152,
+        0x8E: 0x017D, 0x91: 0x2018, 0x92: 0x2019, 0x93: 0x201C,
+        0x94: 0x201D, 0x95: 0x2022, 0x96: 0x2013, 0x97: 0x2014,
+        0x98: 0x02DC, 0x99: 0x2122, 0x9A: 0x0161, 0x9B: 0x203A,
+        0x9C: 0x0153, 0x9E: 0x017E, 0x9F: 0x0178,
+    }
+
     @staticmethod
     def _escape(match: re.Match[str]) -> str:
         codepoint = ord(match.group(0))
+        
+        # Handle Windows-1252 legacy range specially
+        if 0x80 <= codepoint <= 0x9F:
+            # These characters need special handling to avoid HTML parser remapping
+            # Either escape them differently or document the limitation
+            # Option 1: Use hex entities (avoids Windows-1252 interpretation)
+            return f"&#x{codepoint:X};"
+            # Option 2: Accept the remapping as intentional for Windows Help files
+        
         if codepoint in codepoint2name:
             return f"&{codepoint2name[codepoint]};"
         return f"&#{codepoint};"
```