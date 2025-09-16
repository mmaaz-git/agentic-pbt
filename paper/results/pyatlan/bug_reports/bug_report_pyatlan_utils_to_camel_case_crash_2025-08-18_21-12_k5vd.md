# Bug Report: pyatlan.utils.to_camel_case IndexError on Empty/Whitespace Input

**Target**: `pyatlan.utils.to_camel_case`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `to_camel_case` function crashes with IndexError when given empty strings, whitespace-only strings, or strings that become empty after delimiter replacement.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyatlan.utils import to_camel_case

@given(st.text(min_size=1, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
def test_to_camel_case_starts_lowercase(s):
    result = to_camel_case(s)
    if result:
        if result[0].isalpha():
            assert result[0].islower()
```

**Failing input**: `' '`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')
from pyatlan.utils import to_camel_case

to_camel_case(' ')
```

## Why This Is A Bug

The function attempts to access `s[0]` after processing the input, but doesn't check if the resulting string is empty. When the input consists only of delimiters (spaces, underscores, hyphens), the processed string becomes empty, causing an IndexError.

## Fix

```diff
def to_camel_case(s: str) -> str:
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
+   if not s:
+       return s
    return "".join([s[0].lower(), s[1:]])
```