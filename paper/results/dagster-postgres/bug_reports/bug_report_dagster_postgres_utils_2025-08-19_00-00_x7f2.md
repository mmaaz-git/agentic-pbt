# Bug Report: dagster_postgres.utils.get_conn_string URL Encoding Bug

**Target**: `dagster_postgres.utils.get_conn_string`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `get_conn_string` function fails to properly encode forward slashes in usernames and passwords, creating malformed PostgreSQL connection URLs that cannot be parsed correctly.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from urllib.parse import urlparse, unquote
from dagster_postgres.utils import get_conn_string

@given(
    username=st.text(min_size=1, max_size=20),
    password=st.text(min_size=1, max_size=20),
    hostname=st.from_regex(r'^[a-zA-Z0-9.-]+$', fullmatch=True).filter(lambda x: len(x) > 0),
    db_name=st.text(min_size=1, max_size=20).filter(lambda x: not x.isspace())
)
def test_url_round_trip(username, password, hostname, db_name):
    conn_string = get_conn_string(username, password, hostname, db_name)
    parsed = urlparse(conn_string)
    
    if parsed.username:
        assert unquote(parsed.username) == username
    if parsed.password:
        assert unquote(parsed.password) == password
```

**Failing input**: `username='user', password='pass/word', hostname='localhost', db_name='db'`

## Reproducing the Bug

```python
from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse

username = "postgres_user"
password = "secure/pass123"
hostname = "db.example.com"
db_name = "production_db"

conn_string = get_conn_string(username, password, hostname, db_name)
print(f"Generated: {conn_string}")

parsed = urlparse(conn_string)
print(f"Username parsed: {parsed.username}")  # None (should be 'postgres_user')
print(f"Password parsed: {parsed.password}")  # None (should be 'secure/pass123')
print(f"Hostname parsed: {parsed.hostname}")  # 'postgres_user' (wrong!)
```

## Why This Is A Bug

The function uses Python's `quote()` function which doesn't encode forward slashes by default. When credentials contain '/', the resulting URL becomes ambiguous and unparseable. The URL `postgresql://user:pass/word@host:5432/db` is interpreted as having path `/word@host:5432/db` rather than password `pass/word`. This breaks database connectivity for any PostgreSQL deployment using passwords with forward slashes.

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