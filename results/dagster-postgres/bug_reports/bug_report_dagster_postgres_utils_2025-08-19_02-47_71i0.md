# Bug Report: dagster_postgres.utils Improper URL Encoding of Passwords

**Target**: `dagster_postgres.utils.get_conn_string`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `get_conn_string` function improperly encodes passwords containing forward slashes (`/`), resulting in malformed PostgreSQL connection strings that cannot be correctly parsed.

## Property-Based Test

```python
from urllib.parse import quote, unquote, urlparse
from hypothesis import given, strategies as st
from dagster_postgres.utils import get_conn_string

@given(
    username=st.text(min_size=1).filter(lambda x: x),
    password=st.text(min_size=1).filter(lambda x: x),
)
def test_get_conn_string_special_chars_roundtrip(username, password):
    conn_str = get_conn_string(username, password, "localhost", "testdb")
    parsed = urlparse(conn_str)
    
    recovered_username = unquote(parsed.username) if parsed.username else ""
    recovered_password = unquote(parsed.password) if parsed.password else ""
    
    assert recovered_username == username
    assert recovered_password == password
```

**Failing input**: `username='0', password='/'`

## Reproducing the Bug

```python
from urllib.parse import urlparse, unquote
from dagster_postgres.utils import get_conn_string

username = "testuser"
password = "pass/word"
hostname = "localhost"
dbname = "testdb"

conn_str = get_conn_string(username, password, hostname, dbname)
print(f"Connection string: {conn_str}")

parsed = urlparse(conn_str)
recovered_username = unquote(parsed.username) if parsed.username else None
recovered_password = unquote(parsed.password) if parsed.password else None

print(f"Original: username='{username}', password='{password}'")
print(f"Recovered: username='{recovered_username}', password='{recovered_password}'")

assert recovered_username == username
assert recovered_password == password
```

## Why This Is A Bug

The `get_conn_string` function is intended to create valid PostgreSQL connection URLs that can be used to connect to databases. When passwords contain forward slashes, the function generates malformed URLs where the password portion is incorrectly interpreted as part of the URL path. This would prevent users from connecting to their PostgreSQL databases if their passwords contain forward slashes, which is a valid character for PostgreSQL passwords.

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