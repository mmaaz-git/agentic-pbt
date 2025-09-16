# Bug Report: tqdm.utils.disp_trim Incorrect Handling of Negative Lengths

**Target**: `tqdm.utils.disp_trim`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `disp_trim` function does not properly handle negative length values, violating the expected property that trimmed strings should have display length ≤ max(0, requested_length).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from tqdm.utils import disp_trim, disp_len

@given(
    text=st.text(),
    length=st.integers(min_value=-100, max_value=-1)
)
def test_disp_trim_negative_length(text, length):
    """disp_trim should handle negative lengths by trimming to 0."""
    trimmed = disp_trim(text, length)
    actual_display_len = disp_len(trimmed)
    
    # The display length should not exceed 0 for negative requested lengths
    assert actual_display_len <= max(0, length)
```

**Failing input**: `text='hello', length=-1`

## Reproducing the Bug

```python
from tqdm.utils import disp_trim, disp_len

text = 'hello'
length = -1

result = disp_trim(text, length)
display_length = disp_len(result)

print(f"disp_trim('hello', -1) = {result!r}")
print(f"Display length: {display_length}")
print(f"Expected: empty string or display length 0")

# Output:
# disp_trim('hello', -1) = 'hell'
# Display length: 4
# Expected: empty string or display length 0
```

## Why This Is A Bug

The `disp_trim` function is meant to trim strings to a specified display length. When given a negative length, it should reasonably trim to 0 characters (empty string). Instead, it uses Python's negative indexing, resulting in `data[:negative_value]` which trims from the end of the string. This produces unexpected results where negative lengths yield non-empty strings, violating the intuitive contract that negative or zero length should produce minimal output.

## Fix

```diff
def disp_trim(data, length):
    """
    Trim a string which may contain ANSI control characters.
    """
+   # Handle negative lengths by treating them as 0
+   length = max(0, length)
+   
    if len(data) == disp_len(data):
        return data[:length]

    ansi_present = bool(RE_ANSI.search(data))
    while disp_len(data) > length:  # carefully delete one char at a time
        data = data[:-1]
    if ansi_present and bool(RE_ANSI.search(data)):
        # assume ANSI reset is required
        return data if data.endswith("\033[0m") else data + "\033[0m"
    return data
```