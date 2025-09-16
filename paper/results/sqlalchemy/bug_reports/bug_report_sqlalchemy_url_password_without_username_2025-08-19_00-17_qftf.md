# Bug Report: SQLAlchemy URL Password Lost When Username Is None

**Target**: `sqlalchemy.engine.url`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

When creating a URL with a password but no username using URL.create(), the password is lost during the render/parse round-trip.

## Property-Based Test

```python
@given(
    scheme=st.sampled_from(["postgresql", "mysql", "sqlite"]),
    username=st.one_of(st.none(), st.text(alphabet=string.ascii_letters, min_size=1, max_size=10)),
    password=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10)),
    host=st.one_of(st.none(), st.sampled_from(["localhost", "127.0.0.1", "example.com"])),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    database=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20))
)
def test_url_create_vs_make_url(scheme, username, password, host, port, database):
    created_url = URL.create(
        drivername=scheme,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    
    url_string = created_url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    assert created_url.password == parsed_url.password
```

**Failing input**: `username=None, password='0'`

## Reproducing the Bug

```python
from sqlalchemy.engine.url import make_url, URL

created_url = URL.create(
    drivername="postgresql",
    username=None,
    password="mypassword",
    host="localhost",
    database="db"
)

url_string = created_url.render_as_string(hide_password=False)
parsed_url = make_url(url_string)

print(f"Created URL password: {created_url.password}")
print(f"URL string: {url_string}")
print(f"Parsed URL password: {parsed_url.password}")
```

## Why This Is A Bug

The URL.create() API explicitly allows creating URLs with passwords but no usernames. This creates an inconsistency where the API allows creating a URL configuration that cannot survive a round-trip through string representation. While URLs with passwords but no usernames are uncommon, if the API supports creating them, it should preserve them correctly.

## Fix

The render_as_string() method should handle the edge case of password-without-username, possibly by:
1. Including an empty username (`:password@host`) in the rendered string
2. Raising an error when attempting to create such URLs
3. Documenting this limitation clearly

The current silent loss of the password component violates the principle of least surprise and the round-trip property.