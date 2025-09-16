# Bug Report: lxml.doctestcompare Whitespace Normalization Inconsistency

**Target**: `lxml.doctestcompare.LXMLOutputChecker.text_compare`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `text_compare` method incorrectly handles patterns containing certain whitespace characters (like `\r`) when the wildcard `...` is used with `strip=True`, causing valid patterns to fail matching.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import lxml.doctestcompare as dc

@given(st.text(), st.text(), st.text())
def test_text_compare_wildcard(prefix, suffix, middle):
    """Test that ... wildcard matches any text in between"""
    checker = dc.LXMLOutputChecker()
    
    # Build a pattern with wildcard
    pattern = prefix + "..." + suffix
    
    # Build text that should match
    text = prefix + middle + suffix
    
    # The pattern should match the text
    assert checker.text_compare(pattern, text, True)
```

**Failing input**: `prefix='0\r'`, `suffix=''`, `middle=''`

## Reproducing the Bug

```python
import lxml.doctestcompare as dc

checker = dc.LXMLOutputChecker()

pattern = '0\r...'
text = '0\r'

result = checker.text_compare(pattern, text, strip=True)
print(f"Pattern: {pattern!r}")
print(f"Text: {text!r}")
print(f"Expected: True (... should match empty string)")
print(f"Actual: {result}")

assert result, "Pattern '0\\r...' should match '0\\r'"
```

## Why This Is A Bug

The `text_compare` method with `strip=True` should normalize whitespace consistently between the pattern and text. However:

1. The `norm_whitespace` function uses regex `[ \t\n][ \t\n]+` which doesn't include `\r` (carriage return)
2. When processing, `strip()` removes trailing `\r` from the text (making `'0\r'` become `'0'`)
3. But the pattern `'0\r...'` keeps the `\r` after normalization
4. This creates regex `'^0\r.*$'` which doesn't match the stripped text `'0'`

This violates the expected behavior where `...` should match any text including empty strings, and whitespace normalization should be consistent.

## Fix

```diff
--- a/lxml/doctestcompare.py
+++ b/lxml/doctestcompare.py
@@ -69,7 +69,7 @@ def html_fromstring(html):
 
 # We use this to distinguish repr()s from elements:
 _repr_re = re.compile(r'^<[^>]+ (at|object) ')
-_norm_whitespace_re = re.compile(r'[ \t\n][ \t\n]+')
+_norm_whitespace_re = re.compile(r'\s\s+')
 
 class LXMLOutputChecker(OutputChecker):
```

Alternative fix: Apply `norm_whitespace` to both `want` and `got` before stripping in the `text_compare` method, ensuring consistent treatment of all whitespace characters.