# Bug Report: django.http.parse_cookie Data Loss with Whitespace Values

**Target**: `django.http.parse_cookie`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `parse_cookie` function incorrectly strips all whitespace-only values to empty strings, causing data loss for cookies containing only whitespace characters including non-breaking spaces.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import django.http

cookie_value = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'),
        blacklist_characters=';,\\\"\x00\r\n'
    ),
    max_size=100
)

@given(st.dictionaries(cookie_name, cookie_value, min_size=1, max_size=10))
def test_parse_cookie_basic(cookies):
    cookie_parts = [f"{name}={value}" for name, value in cookies.items()]
    cookie_string = '; '.join(cookie_parts)
    parsed = django.http.parse_cookie(cookie_string)
    for name, value in cookies.items():
        assert name in parsed
        assert parsed[name] == value
```

**Failing input**: `cookies={'0': '\xa0'}`

## Reproducing the Bug

```python
import django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='test', DEFAULT_CHARSET='utf-8')

import django.http

cookie_with_nbsp = "session_id=\xa0"
parsed = django.http.parse_cookie(cookie_with_nbsp)

print(f"Input: {repr(cookie_with_nbsp)}")
print(f"Parsed value: {repr(parsed['session_id'])}")

assert parsed['session_id'] == '\xa0', f"Expected '\\xa0', got {repr(parsed['session_id'])}"
```

## Why This Is A Bug

The function silently transforms whitespace-only values into empty strings, causing data loss. Non-breaking spaces (\xa0) and other whitespace characters may be semantically meaningful in certain applications. A parser should preserve the original data or explicitly document this limitation.

## Fix

The issue likely stems from overly aggressive whitespace stripping in the cookie parsing logic. The fix would involve preserving the original value when it consists entirely of whitespace characters, or at minimum documenting this behavior in the function's docstring.