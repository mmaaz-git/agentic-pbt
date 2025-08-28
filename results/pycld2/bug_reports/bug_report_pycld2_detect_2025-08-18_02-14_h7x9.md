# Bug Report: pycld2.detect textBytesFound Reports 2 Extra Bytes

**Target**: `pycld2.detect`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `textBytesFound` field returned by `pycld2.detect()` consistently reports 2 more bytes than the actual UTF-8 byte length of the input text, appearing to count null terminators that aren't part of the input.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pycld2

@given(st.text(min_size=1, max_size=1000))
def test_text_bytes_found_invariant(text):
    # Skip special cases where pycld2 returns 0 bytes
    if text.strip() == '' or all(ord(c) > 127 and ord(c) not in range(0x4E00, 0x9FFF) for c in text):
        return
    
    result = pycld2.detect(text)
    text_bytes_found = result[1]
    text_bytes_len = len(text.encode('utf-8'))
    
    assert text_bytes_found <= text_bytes_len, f"textBytesFound ({text_bytes_found}) > actual bytes ({text_bytes_len})"
```

**Failing input**: `"A"`

## Reproducing the Bug

```python
import pycld2

text = "A"
result = pycld2.detect(text)
text_bytes_found = result[1]
actual_bytes = len(text.encode('utf-8'))

print(f"Input text: {repr(text)}")
print(f"Actual UTF-8 bytes: {actual_bytes}")
print(f"textBytesFound: {text_bytes_found}")
print(f"Difference: {text_bytes_found - actual_bytes}")

assert text_bytes_found == actual_bytes, f"Expected {actual_bytes} bytes, got {text_bytes_found}"
```

## Why This Is A Bug

The `textBytesFound` field is documented as "Total number of bytes of text detected" but it consistently reports 2 extra bytes beyond the actual UTF-8 byte length of the input. This violates the expected behavior where the detected bytes should not exceed the input bytes. The pattern suggests the library is counting C-style double null terminators that are used internally but should not be included in the byte count reported to users.

## Fix

The bug appears to be in the C++ implementation where the byte counting includes internal null terminators. A high-level fix would involve:

1. Adjusting the byte counting logic in the underlying C++ code to exclude null terminators from the reported count
2. Ensuring `textBytesFound` reflects only the actual text bytes processed, not internal string representation overhead

The consistent 2-byte offset suggests this is a systematic issue in how the library counts bytes, likely related to C-style string handling with double null termination.