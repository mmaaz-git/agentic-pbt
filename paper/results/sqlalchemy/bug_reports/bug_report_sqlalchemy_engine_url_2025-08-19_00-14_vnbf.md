# Bug Report: sqlalchemy.engine URL Empty Password Loss

**Target**: `sqlalchemy.engine.url.URL`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

When creating a URL with `username=None` and an empty string password (`password=''`), the password is lost during round-trip parsing and becomes `None`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqlalchemy.engine import make_url
from sqlalchemy.engine.url import URL

@given(
    drivername=st.sampled_from(['postgresql', 'mysql', 'sqlite']),
    username=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    password=st.one_of(st.none(), st.text(min_size=0, max_size=10)),
    host=st.one_of(st.none(), st.just('localhost')),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    database=st.one_of(st.none(), st.text(min_size=0, max_size=10))
)
def test_url_create_round_trip(drivername, username, password, host, port, database):
    url = URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query={}
    )
    
    url_string = url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    assert parsed_url.password == password
```

**Failing input**: `drivername='postgresql', username=None, password='', host=None, port=None, database=None`

## Reproducing the Bug

```python
from sqlalchemy.engine.url import URL
from sqlalchemy.engine import make_url

url = URL.create(
    drivername='postgresql',
    username=None,
    password='',
    host=None,
    port=None,
    database=None,
    query={}
)

url_string = url.render_as_string(hide_password=False)
parsed_url = make_url(url_string)

print(f"Original password: {repr(url.password)}")
print(f"Parsed password: {repr(parsed_url.password)}")
print(f"Match: {url.password == parsed_url.password}")
```

## Why This Is A Bug

The URL.create method explicitly accepts an empty string as a valid password value, distinct from None. When this URL is converted to a string and parsed back, the empty string password is lost and becomes None. This violates the round-trip property that parsing and rendering a URL should preserve all its components. Some database configurations may use empty passwords (especially in development environments), and this information loss could cause authentication failures.

## Fix

The issue occurs because when `username=None` and `password=''`, the URL is rendered without any authentication section (e.g., `postgresql://`). The fix would involve modifying the render logic to preserve empty passwords when present:

```diff
# In URL.render_as_string or related rendering logic
- if self.username is not None:
+ if self.username is not None or self.password is not None:
     # Include authentication section even if username is None but password is set
     if self.username is None:
         s += ':'  # Start with colon for empty username
     else:
         s += _rfc_1738_quote(self.username)
     if self.password is not None:
         s += ':' + (self.password if not hide_password else '***')
     s += '@'
```