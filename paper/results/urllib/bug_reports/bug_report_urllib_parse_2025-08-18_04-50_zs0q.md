# Bug Report: urllib.parse Empty Value Data Loss in Query String Round-Trip

**Target**: `urllib.parse.urlencode` / `urllib.parse.parse_qs` / `urllib.parse.parse_qsl`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The round-trip of encoding and decoding query strings loses data when values are empty strings, violating the expected property that `parse_qs(urlencode(data))` should preserve all keys from the original data.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import urllib.parse

@given(st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(blacklist_characters='&=\x00\ud800-\udfff')),
    st.text(alphabet=st.characters(blacklist_characters='&=\x00\ud800-\udfff')),
    min_size=1,
    max_size=10
))
def test_urlencode_parse_qs_round_trip(data):
    encoded = urllib.parse.urlencode(data)
    decoded = urllib.parse.parse_qs(encoded)
    
    # All keys from original data should be preserved
    assert set(data.keys()).issubset(set(decoded.keys()))
```

**Failing input**: `{'username': 'alice', 'password': ''}`

## Reproducing the Bug

```python
import urllib.parse

data = {'username': 'alice', 'password': ''}
encoded = urllib.parse.urlencode(data)
print(f"Encoded: {encoded}")

decoded = urllib.parse.parse_qs(encoded)
print(f"Decoded: {decoded}")
print(f"Lost keys: {set(data.keys()) - set(decoded.keys())}")

assert 'password' in decoded
```

## Why This Is A Bug

This violates the principle of data preservation in encoding/decoding operations. Empty values are valid in HTTP query strings and HTML forms - for example, unchecked checkboxes or optional fields left blank. The current behavior causes silent data loss that can lead to:

1. **Form submission bugs**: Optional fields with empty values disappear completely
2. **API inconsistencies**: REST APIs that accept empty string parameters lose them in processing
3. **Data integrity issues**: Round-trip operations alter the data structure unexpectedly

The asymmetry between `urlencode` (which correctly encodes empty values as `key=`) and `parse_qs`/`parse_qsl` (which drop them by default) is problematic for any system expecting round-trip consistency.

## Fix

The issue stems from the default `keep_blank_values=False` parameter in `parse_qs` and `parse_qsl`. While changing the default would break backward compatibility, the documentation should prominently warn about this data loss risk and recommend using `keep_blank_values=True` for round-trip scenarios.

A documentation fix would add a warning like:

```diff
def parse_qs(qs, keep_blank_values=False, strict_parsing=False,
             encoding='utf-8', errors='replace', max_num_fields=None,
             separator='&'):
     """Parse a query given as a string argument.
 
     Arguments:
 
     qs: percent-encoded query string to be parsed
 
     keep_blank_values: flag indicating whether blank values in
         percent-encoded queries should be treated as blank strings.
         A true value indicates that blanks should be retained as
         blank strings.  The default false value indicates that
         blank values are to be ignored and treated as if they were
-        not included.
+        not included. WARNING: This default behavior breaks round-trip
+        compatibility with urlencode() for dictionaries containing empty
+        string values. Use keep_blank_values=True to preserve all keys.
```