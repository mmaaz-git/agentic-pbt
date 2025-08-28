# Bug Report: dagster_postgres.utils Improper URL Encoding in get_conn_string

**Target**: `dagster_postgres.utils.get_conn_string`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `get_conn_string` function fails to properly encode special characters in usernames and passwords, causing malformed PostgreSQL connection URLs that break URL parsing and prevent database connections.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from urllib.parse import urlparse, unquote

@given(
    username=st.text(min_size=1).filter(lambda x: "/" in x),
    password=st.text(min_size=1).filter(lambda x: "/" in x)
)
def test_get_conn_string_handles_special_chars(username, password):
    conn_string = get_conn_string(
        username=username,
        password=password,
        hostname="localhost",
        db_name="testdb",
        port="5432"
    )
    
    parsed = urlparse(conn_string)
    assert parsed.hostname == "localhost"
    assert unquote(parsed.username) == username
    assert unquote(parsed.password) == password
```

**Failing input**: `username="user", password="pass/word"`

## Reproducing the Bug

```python
from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse

conn_string = get_conn_string(
    username="user",
    password="pass/word",
    hostname="localhost",
    db_name="testdb",
    port="5432"
)

print(f"Generated: {conn_string}")
# Output: postgresql://user:pass/word@localhost:5432/testdb

parsed = urlparse(conn_string)
print(f"Hostname: {parsed.hostname}")  # Returns 'user' instead of 'localhost'
print(f"Password: {parsed.password}")  # Returns None
```

## Why This Is A Bug

The forward slash in the password is not percent-encoded, causing the URL parser to misinterpret the URL structure. The slash is treated as a path separator, corrupting the entire URL. This prevents users from using passwords containing forward slashes, at-signs, colons, or other special URL characters, which is a common requirement in secure environments.

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