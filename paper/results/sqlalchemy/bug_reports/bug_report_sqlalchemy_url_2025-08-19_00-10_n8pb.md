# Bug Report: SQLAlchemy URL Special Characters Lost in Round-Trip

**Target**: `sqlalchemy.engine.url`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

URL passwords containing special characters are URL-encoded when rendered, breaking the round-trip property between `make_url()` and `render_as_string()`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqlalchemy.engine import url

@given(st.text(alphabet='$#@!%&*()+=-', min_size=1, max_size=10))
def test_url_password_special_chars(password):
    url_string = f'postgresql://user:{password}@localhost/db'
    parsed = url.make_url(url_string)
    rendered = parsed.render_as_string(hide_password=False)
    assert url_string == rendered
```

**Failing input**: `postgresql://user:$@localhost/db`

## Reproducing the Bug

```python
from sqlalchemy.engine import url

original = 'postgresql://user:$@localhost/db'
parsed = url.make_url(original)
rendered = parsed.render_as_string(hide_password=False)

print(f'Original:  {original}')
print(f'Rendered:  {rendered}')
print(f'Equal? {original == rendered}')

# Output:
# Original:  postgresql://user:$@localhost/db
# Rendered:  postgresql://user:%24@localhost/db
# Equal? False
```

## Why This Is A Bug

The documentation implies that `make_url()` accepts RFC-1738 format URLs and that URLs can be round-tripped. Users expect that a valid URL string passed to `make_url()` would be preserved when rendered back with `hide_password=False`. This breaks that expectation and can cause issues when URLs are stored and retrieved.

## Fix

The issue appears to be that `render_as_string()` URL-encodes special characters in passwords even though `make_url()` accepts them unencoded. Either:

1. `make_url()` should require URL-encoded passwords, or
2. `render_as_string()` should preserve the original format when `hide_password=False`

A potential fix would be to track whether the original password was URL-encoded and preserve that format when rendering.