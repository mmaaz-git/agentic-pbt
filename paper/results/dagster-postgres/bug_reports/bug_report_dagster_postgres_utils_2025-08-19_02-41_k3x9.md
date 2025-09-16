# Bug Report: dagster_postgres.utils URL Generation Breaks with Special Characters in Passwords

**Target**: `dagster_postgres.utils.get_conn_string`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `get_conn_string` function incorrectly encodes passwords containing URL delimiter characters (`:`, `/`, `@`), resulting in malformed connection strings that cannot be parsed correctly.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from urllib.parse import urlparse
from dagster_postgres.utils import get_conn_string

@given(
    username=st.text(min_size=1, max_size=50),
    password=st.text(min_size=1, max_size=50),
    hostname=st.text(min_size=1, max_size=50),
    db_name=st.text(min_size=1, max_size=50),
    port=st.integers(min_value=1, max_value=65535).map(str)
)
def test_conn_string_can_be_parsed(username, password, hostname, db_name, port):
    conn_string = get_conn_string(username, password, hostname, db_name, port)
    parsed = urlparse(conn_string)
    assert parsed.scheme == "postgresql"
    assert parsed.hostname == hostname.lower()
    assert parsed.port == int(port)
    assert parsed.path == f"/{db_name}"
```

**Failing input**: `password=":/", hostname="localhost", username="user", db_name="test", port="5432"`

## Reproducing the Bug

```python
from urllib.parse import urlparse
from dagster_postgres.utils import get_conn_string

# Password with colon and slash breaks URL parsing
conn_str = get_conn_string(
    username="user",
    password=":/",
    hostname="localhost",
    db_name="testdb",
    port="5432"
)

print(f"Generated: {conn_str}")
# Output: postgresql://user:%3A/@localhost:5432/testdb

parsed = urlparse(conn_str)
print(f"Parsed hostname: {parsed.hostname}")
# Output: user (WRONG - should be localhost)

print(f"Parsed port: {parsed.port}")
# Raises: ValueError: Port could not be cast to integer value as '%3A'
```

## Why This Is A Bug

The `quote()` function by default does not encode characters like `:`, `/`, and `@` because they are considered "safe" for URLs. However, when these characters appear in the password field of a connection string, they must be encoded to avoid ambiguity with URL delimiters. The current implementation creates malformed URLs that:

1. Cannot be parsed correctly by standard URL parsers
2. May connect to the wrong host or database
3. Will fail when passed to PostgreSQL connection libraries

## Fix

```diff
--- a/dagster_postgres/utils.py
+++ b/dagster_postgres/utils.py
@@ -59,7 +59,7 @@ def get_conn_string(
     params: Optional[Mapping[str, object]] = None,
     scheme: str = "postgresql",
 ) -> str:
-    uri = f"{scheme}://{quote(username)}:{quote(password)}@{hostname}:{port}/{db_name}"
+    uri = f"{scheme}://{quote(username, safe='')}:{quote(password, safe='')}@{hostname}:{port}/{db_name}"
 
     if params:
         query_string = f"{urlencode(params, quote_via=quote)}"
```