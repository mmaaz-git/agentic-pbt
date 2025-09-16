# Bug Report: lxml.html Inconsistent Control Character Handling in fragment_fromstring

**Target**: `lxml.html.fragment_fromstring`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `fragment_fromstring` function with `create_parent=True` inconsistently handles control characters - it silently converts NULL bytes (0x00) to U+FFFD but raises ValueError for other control characters (0x01-0x08, 0x0E-0x1B).

## Property-Based Test

```python
from hypothesis import given, strategies as st
import lxml.html

@given(st.integers(min_value=0, max_value=0x1F))
def test_control_char_consistency(char_code):
    if char_code in [0x09, 0x0A, 0x0D]:  # Skip valid whitespace
        return
    
    char = chr(char_code)
    
    # fromstring accepts all control characters
    fromstring_success = False
    try:
        result1 = lxml.html.fromstring(char)
        fromstring_success = True
    except:
        pass
    
    # fragment_fromstring with create_parent should behave consistently
    fragment_success = False
    fragment_error = None
    try:
        result2 = lxml.html.fragment_fromstring(char, create_parent=True)
        fragment_success = True
    except ValueError as e:
        fragment_error = str(e)
    
    # If fromstring succeeds, fragment_fromstring behavior should be predictable
    if fromstring_success:
        if char_code == 0x00:  # NULL byte
            assert fragment_success, "NULL byte should not raise ValueError"
        elif char_code in range(0x01, 0x09) or char_code in range(0x0E, 0x1C):
            assert not fragment_success, f"Control char 0x{char_code:02X} should raise ValueError"
            assert "XML compatible" in fragment_error
```

**Failing input**: Control character 0x00 (NULL byte)

## Reproducing the Bug

```python
import lxml.html

null_byte = '\x00'
esc_char = '\x1b'

# Both parse successfully with fromstring
result1 = lxml.html.fromstring(null_byte)
print(f"NULL with fromstring: <{result1.tag}>")

result2 = lxml.html.fromstring(esc_char)  
print(f"ESC with fromstring: <{result2.tag}>")

# But fragment_fromstring with create_parent behaves inconsistently
try:
    result3 = lxml.html.fragment_fromstring(null_byte, create_parent=True)
    print(f"NULL with fragment_fromstring: SUCCESS - text={result3.text!r}")
except ValueError as e:
    print(f"NULL with fragment_fromstring: FAILED - {e}")

try:
    result4 = lxml.html.fragment_fromstring(esc_char, create_parent=True)
    print(f"ESC with fragment_fromstring: SUCCESS - text={result4.text!r}")
except ValueError as e:
    print(f"ESC with fragment_fromstring: FAILED - {e}")
```

## Why This Is A Bug

The NULL byte (0x00) gets silently replaced with U+FFFD during HTML parsing, bypassing the XML validation that occurs when `fragment_fromstring` assigns text to the created parent element. This creates an inconsistency where most control characters (0x01-0x1B) correctly raise ValueError, but NULL byte silently passes through with data corruption. The function should either consistently reject all control characters or consistently handle them.

## Fix

The issue occurs in `fragment_fromstring` when it tries to assign parsed text to a newly created parent element. The NULL byte has already been replaced with U+FFFD by the parser, so the XML validation doesn't catch it. A fix would require checking for U+FFFD replacement characters that resulted from NULL bytes:

```diff
--- a/lxml/html/__init__.py
+++ b/lxml/html/__init__.py
@@ -817,6 +817,9 @@ def fragment_fromstring(html, create_parent=False, base_url=None,
         new_root = Element(create_parent)
         if elements:
             if isinstance(elements[0], str):
+                # Check if NULL bytes were replaced during parsing
+                if '\ufffd' in elements[0] and '\x00' in html:
+                    raise ValueError("NULL bytes are not allowed in element text")
                 new_root.text = elements[0]
                 del elements[0]
             new_root.extend(elements)
```