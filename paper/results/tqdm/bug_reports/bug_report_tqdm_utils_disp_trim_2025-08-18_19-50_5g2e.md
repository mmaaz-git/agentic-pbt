# Bug Report: tqdm.utils.disp_trim Incomplete ANSI Code Handling

**Target**: `tqdm.utils.disp_trim`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The disp_trim function can produce malformed output containing partial ANSI escape sequences without proper reset codes when trimming strings with multiple ANSI codes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from tqdm.utils import disp_trim, disp_len

@given(
    text=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    ansi_codes=st.lists(
        st.sampled_from(['\x1b[31m', '\x1b[32m', '\x1b[1m']),
        min_size=1,
        max_size=3
    ),
    trim_length=st.integers(min_value=1, max_value=50)
)
def test_disp_trim_ansi_reset(text, ansi_codes, trim_length):
    text_with_ansi = ansi_codes[0] + text
    for code in ansi_codes[1:]:
        pos = len(text_with_ansi) // 2
        text_with_ansi = text_with_ansi[:pos] + code + text_with_ansi[pos:]
    
    trimmed = disp_trim(text_with_ansi, trim_length)
    
    if '\x1b[' in text_with_ansi and disp_len(text_with_ansi) > trim_length:
        if '\x1b[' in trimmed:
            assert trimmed.endswith('\x1b[0m'), "disp_trim didn't add ANSI reset code"
```

**Failing input**: `text='0', ansi_codes=['\x1b[31m', '\x1b[31m'], trim_length=2`

## Reproducing the Bug

```python
from tqdm.utils import disp_trim, disp_len

text = '0'
ansi_codes = ['\x1b[31m', '\x1b[31m']
text_with_ansi = '\x1b[31m' + text
pos = len(text_with_ansi) // 2
text_with_ansi = text_with_ansi[:pos] + '\x1b[31m' + text_with_ansi[pos:]

trimmed = disp_trim(text_with_ansi, 2)
print(repr(trimmed))  # '\x1b[' - incomplete ANSI sequence without reset
```

## Why This Is A Bug

When disp_trim truncates a string containing ANSI escape codes, it can cut in the middle of an escape sequence, producing malformed output like `'\x1b['` without the complete sequence. Additionally, when ANSI codes are present but incomplete after trimming, the function fails to append the ANSI reset code `\x1b[0m` as intended, which can cause terminal display issues.

## Fix

The function needs to handle partial ANSI sequences more carefully, either by:
1. Ensuring complete ANSI sequences are preserved or removed entirely
2. Always adding reset codes when any ANSI sequence (even partial) remains
3. Stripping incomplete ANSI sequences from the output

```diff
--- a/tqdm/utils.py
+++ b/tqdm/utils.py
@@ -394,8 +394,13 @@ def disp_trim(data, length):
     while disp_len(data) > length:
         data = data[:-1]
     if ansi_present and bool(RE_ANSI.search(data)):
         # assume ANSI reset is required
         return data if data.endswith("\033[0m") else data + "\033[0m"
+    elif ansi_present and '\x1b[' in data:
+        # Partial ANSI sequence remains, add reset
+        return data + "\033[0m"
     return data
```