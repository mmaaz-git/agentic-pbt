# Bug Report: SQLAlchemy URL Query Parameters with Empty Values Lost During Round-Trip

**Target**: `sqlalchemy.engine.url`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

URL query parameters with empty string values are lost when a URL is rendered to string and parsed back, violating the round-trip property.

## Property-Based Test

```python
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(min_size=0, max_size=20),
        min_size=1,
        max_size=5
    )
)
def test_url_query_params_special_chars(params):
    original_url = URL.create(
        drivername="postgresql",
        host="localhost",
        database="db",
        query=params
    )
    
    url_string = original_url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    assert parsed_url.query == original_url.query
```

**Failing input**: `params={'0': ''}`

## Reproducing the Bug

```python
from sqlalchemy.engine.url import make_url, URL

original_url = URL.create(
    drivername="postgresql",
    host="localhost",
    database="db",
    query={'key': ''}
)

url_string = original_url.render_as_string(hide_password=False)
parsed_url = make_url(url_string)

print(f"Original query: {original_url.query}")
print(f"URL string: {url_string}")
print(f"Parsed query: {parsed_url.query}")
```

## Why This Is A Bug

Query parameters with empty values are valid in URLs and have semantic meaning (e.g., `?debug=` to enable debug mode). The round-trip property should preserve all URL components exactly as created. Losing empty-valued parameters changes the URL's meaning and breaks applications that rely on their presence.

## Fix

The issue appears to be in the URL parsing logic which treats `key=` (empty value) as equivalent to no parameter. The parser should distinguish between:
- `?key=` (parameter with empty value)
- No `key` parameter at all

The parsing logic should preserve empty string values in query parameters to maintain full round-trip fidelity.