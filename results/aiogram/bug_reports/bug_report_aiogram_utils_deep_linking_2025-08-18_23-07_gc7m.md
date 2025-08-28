# Bug Report: aiogram.utils.deep_linking Length Check Applied After Encoding

**Target**: `aiogram.utils.deep_linking.create_deep_link`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `create_deep_link` function incorrectly applies the 64-character limit to the encoded payload instead of the original payload, causing legitimate short strings to fail when `encode=True`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import aiogram.utils.deep_linking as dl

@given(st.text(min_size=1))
def test_deep_link_encoded_payload_accepts_any_string(text):
    """Test that create_deep_link with encode=True accepts any reasonable string"""
    link = dl.create_deep_link(
        username="testbot",
        link_type="start",
        payload=text,
        encode=True
    )
    assert isinstance(link, str)
    assert "testbot" in link
```

**Failing input**: `'00000\x80\x80\x80\x80\x80\x80\x80\x80𐀀𐀀𐀀𐀀𐀀𐀀𐀀'`

## Reproducing the Bug

```python
import aiogram.utils.deep_linking as dl

text = "0" * 5 + "\x80" * 8 + "𐀀" * 7  

link = dl.create_deep_link(
    username="testbot",
    link_type="start",
    payload=text,
    encode=True
)
```

## Why This Is A Bug

The function applies the 64-character limit after encoding the payload with base64, not before. Base64 encoding expands string length by 1.33x for ASCII and up to 5.4x for 4-byte Unicode characters. This means even a 12-character string of emojis or special Unicode can fail, despite being well within reasonable limits.

The `encode=True` parameter exists specifically to handle arbitrary strings by encoding them, but the current implementation defeats this purpose by rejecting many valid inputs after encoding.

## Fix

```diff
--- a/aiogram/utils/deep_linking.py
+++ b/aiogram/utils/deep_linking.py
@@ -127,6 +127,10 @@ def create_deep_link(
     if not isinstance(payload, str):
         payload = str(payload)
 
+    # Check length before encoding, not after
+    if not (encode or encoder) and len(payload) > 64:
+        raise ValueError("Payload must be up to 64 characters long.")
+
     if encode or encoder:
         payload = encode_payload(payload, encoder=encoder)
 
@@ -136,9 +140,10 @@ def create_deep_link(
             "Pass `encode=True` or encode payload manually."
         )
 
-    if len(payload) > 64:
-        raise ValueError("Payload must be up to 64 characters long.")
-
+    # After encoding, check if the result still fits in Telegram's limits
+    if len(payload) > 64:
+        raise ValueError("Encoded payload exceeds 64 characters. Consider using a shorter input.")
+
     if not app_name:
         deep_link = create_telegram_link(username, **{cast(str, link_type): payload})
     else:
```