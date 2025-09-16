# Bug Report: RequestsCookieJar Empty String Values Lost

**Target**: `requests.cookies.RequestsCookieJar`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

RequestsCookieJar silently loses cookie values that are empty strings, returning None instead of the actual empty string value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.cookies import RequestsCookieJar

@given(st.text(min_size=0, max_size=1))
def test_set_get_consistency(value):
    jar = RequestsCookieJar()
    jar.set('test', value)
    assert jar.get('test') == value
```

**Failing input**: `value=''`

## Reproducing the Bug

```python
from requests.cookies import RequestsCookieJar

jar = RequestsCookieJar()
jar.set('test', '')
result = jar.get('test')
print(f"Expected: {''!r}")
print(f"Actual: {result!r}")
assert result == '', f"Cookie value lost: expected '' but got {result!r}"
```

## Why This Is A Bug

The RequestsCookieJar is documented to act like a dictionary, but it fails to preserve empty string values. This violates the fundamental property that setting and getting a value should return the same value. Empty strings are valid cookie values according to RFC 6265, and silently converting them to None causes data loss.

## Fix

The bug is in the `_find_no_duplicates` method which incorrectly uses truthiness check instead of None check:

```diff
--- a/requests/cookies.py
+++ b/requests/cookies.py
@@ -408,7 +408,7 @@ class RequestsCookieJar(cookielib.CookieJar, MutableMapping):
                         # we will eventually return this as long as no cookie conflict
                         toReturn = cookie.value
 
-        if toReturn:
+        if toReturn is not None:
             return toReturn
         raise KeyError(f"name={name!r}, domain={domain!r}, path={path!r}")
```