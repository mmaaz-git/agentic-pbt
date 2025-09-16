# Bug Report: django.utils.encoding IRI/URI Round-Trip Failure

**Target**: `django.utils.encoding.iri_to_uri` and `django.utils.encoding.uri_to_iri`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The IRI to URI conversion functions do not properly round-trip for many ASCII characters. Characters like quotes, spaces, and brackets get percent-encoded by `iri_to_uri` but are not decoded back by `uri_to_iri`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.utils import encoding

@given(st.text(min_size=1, max_size=100).filter(lambda s: all(ord(c) < 128 for c in s)))
def test_iri_uri_roundtrip_ascii(iri):
    """For ASCII input, IRI to URI and back should preserve the input"""
    uri = encoding.iri_to_uri(iri)
    back = encoding.uri_to_iri(uri)
    assert back == iri
```

**Failing input**: `'"'`

## Reproducing the Bug

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='test')

from django.utils import encoding

# Characters that fail to round-trip
failing_chars = ['"', ' ', '<', '>', '{', '}', '|', '\\', '^', '`']

for char in failing_chars:
    uri = encoding.iri_to_uri(char)
    back = encoding.uri_to_iri(uri)
    print(f'{repr(char)} -> {repr(uri)} -> {repr(back)}')
    assert back == char, f"Round-trip failed: {char} != {back}"
```

## Why This Is A Bug

The functions `iri_to_uri` and `uri_to_iri` are documented as converting between IRI and URI representations. Users reasonably expect these to be inverse operations for valid inputs. However, the current implementation breaks this expectation for common ASCII characters.

The issue stems from `uri_to_iri` using a selective decoding strategy via the `_hextobyte` dictionary, which only includes:
- RFC 3986 unreserved characters: `-._~A-Za-z0-9`
- Bytes ≥ 128 for multibyte Unicode

This excludes many ASCII characters that `iri_to_uri` percent-encodes, preventing proper round-trip conversion.

## Fix

```diff
--- a/django/utils/encoding.py
+++ b/django/utils/encoding.py
@@ -138,11 +138,13 @@
 # List of byte values that uri_to_iri() decodes from percent encoding.
 # First, the unreserved characters from RFC 3986:
 _ascii_ranges = [[45, 46, 95, 126], range(65, 91), range(97, 123)]
 _hextobyte = {
     (fmt % char).encode(): bytes((char,))
     for ascii_range in _ascii_ranges
     for char in ascii_range
     for fmt in ["%02x", "%02X"]
 }
+# Add all ASCII characters that might have been percent-encoded
+_hextobyte.update({(fmt % char).encode(): bytes((char,)) for char in range(32, 127) for fmt in ["%02x", "%02X"]})
 # And then everything above 128, because bytes ≥ 128 are part of multibyte
 # Unicode characters.
```