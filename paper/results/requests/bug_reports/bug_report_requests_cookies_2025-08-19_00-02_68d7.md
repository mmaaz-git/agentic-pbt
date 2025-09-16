# Bug Report: RequestsCookieJar AttributeError with domain=None

**Target**: `requests.cookies.create_cookie`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The create_cookie function crashes with AttributeError when explicitly passed domain=None, which should be a valid way to specify no domain restriction.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from requests.cookies import RequestsCookieJar

@given(
    st.text(min_size=1, max_size=10),
    st.text(min_size=0, max_size=10),
    st.one_of(st.none(), st.text(min_size=1, max_size=10))
)
def test_set_with_optional_domain(name, value, domain):
    jar = RequestsCookieJar()
    jar.set(name, value, domain=domain)
    assert jar.get(name, domain=domain) == value
```

**Failing input**: `name='0', value='', domain=None`

## Reproducing the Bug

```python
from requests.cookies import RequestsCookieJar

jar = RequestsCookieJar()
jar.set('test', 'value', domain=None)
```

## Why This Is A Bug

The set() method accepts an optional domain parameter that should handle None gracefully to mean "no specific domain". Instead, the create_cookie function unconditionally calls .startswith() on the domain value without checking if it's None first. This causes a crash instead of handling the None case properly.

## Fix

The bug is in the create_cookie function which doesn't check for None before calling string methods:

```diff
--- a/requests/cookies.py
+++ b/requests/cookies.py
@@ -483,7 +483,8 @@ def create_cookie(name, value, **kwargs):
     rest = {"HttpOnly": None}
 
     result = {
-        "domain_initial_dot": result["domain"].startswith("."),
+        "domain": kwargs.get("domain") or "",
+        "domain_initial_dot": bool(kwargs.get("domain") and kwargs.get("domain").startswith(".")),
         "name": name,
         "value": value,
     }
```