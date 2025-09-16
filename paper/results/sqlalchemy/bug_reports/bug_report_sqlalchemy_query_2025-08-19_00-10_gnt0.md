# Bug Report: SQLAlchemy URL Query Parameters with Empty Values Lost

**Target**: `sqlalchemy.engine.url`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Query parameters with empty string values are silently dropped during URL round-trip operations, causing data loss.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sqlalchemy.engine import url

@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.just(''),  # Empty string values
    min_size=1,
    max_size=5
))
def test_url_empty_query_params(params):
    base_url = url.URL.create(
        drivername='postgresql',
        host='localhost',
        database='testdb',
        query=params
    )
    url_string = base_url.render_as_string(hide_password=False)
    parsed_url = url.make_url(url_string)
    
    for key in params:
        assert key in parsed_url.query
        assert parsed_url.query[key] == params[key]
```

**Failing input**: `{'key1': ''}`

## Reproducing the Bug

```python
from sqlalchemy.engine import url

base_url = url.URL.create(
    drivername='postgresql',
    host='localhost',
    database='testdb',
    query={'key1': '', 'key2': 'value2'}
)

url_string = base_url.render_as_string()
parsed_url = url.make_url(url_string)

print(f'Original query: {base_url.query}')
print(f'Parsed query:   {parsed_url.query}')
print(f'key1 preserved? {"key1" in parsed_url.query}')

# Output:
# Original query: immutabledict({'key1': '', 'key2': 'value2'})
# Parsed query:   immutabledict({'key2': 'value2'})
# key1 preserved? False
```

## Why This Is A Bug

Query parameters with empty values are valid and semantically different from absent parameters. Many web APIs distinguish between:
- `?param=` (parameter present with empty value)
- No parameter at all

The current behavior silently drops these parameters, causing data loss and potentially changing the meaning of the URL.

## Fix

The URL rendering or parsing logic should preserve query parameters with empty string values. The issue likely occurs during URL string generation where empty-valued parameters are skipped. The fix would involve:

```diff
# In render_as_string or URL string generation:
- if value:  # Skip empty values
-     query_parts.append(f"{key}={value}")
+ if value is not None:  # Preserve empty strings
+     query_parts.append(f"{key}={value}")
```