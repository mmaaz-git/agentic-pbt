# Bug Report: pyatlan.utils.to_camel_case Non-Idempotent Transformation

**Target**: `pyatlan.utils.to_camel_case`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `to_camel_case` function is not idempotent - applying it twice to certain inputs produces different results than applying it once.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyatlan.utils import to_camel_case

@given(st.text(min_size=1, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
def test_to_camel_case_idempotence(s):
    first_conversion = to_camel_case(s)
    second_conversion = to_camel_case(first_conversion)
    assert first_conversion == second_conversion
```

**Failing input**: `'A A'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')
from pyatlan.utils import to_camel_case

s = 'A A'
first = to_camel_case(s)
second = to_camel_case(first)
print(f'First: {first}')   # Output: 'aA'
print(f'Second: {second}')  # Output: 'aa'
```

## Why This Is A Bug

The function converts 'A A' to 'aA' on first application. When applied again, it incorrectly treats the capital 'A' in 'aA' as a word boundary (since there's no delimiter), converting it to lowercase, resulting in 'aa'. This violates the expectation that camelCase strings should remain unchanged when the function is applied again.

## Fix

The issue is that the function doesn't recognize already camelCased strings. A proper fix would require detecting if the input is already in camelCase format and returning it unchanged, or adjusting the regex to not treat uppercase letters within words as boundaries. A simple approach:

```diff
def to_camel_case(s: str) -> str:
+   # If already in camelCase (no delimiters), return as-is with first char lowercase
+   if not re.search(r"[_\- ]", s):
+       return s[0].lower() + s[1:] if s else s
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
    if not s:
        return s
    return "".join([s[0].lower(), s[1:]])
```