# Bug Report: dagster_postgres.utils get_conn_string Special Character Handling

**Target**: `dagster_postgres.utils.get_conn_string`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-01-19

## Summary

The `get_conn_string` function incorrectly handles special characters in passwords, hostnames, and database names, producing malformed URLs that cannot be parsed or that lose data.

## Property-Based Test

```python
@given(
    username=st.text(min_size=1),
    password=st.text(min_size=1),
    hostname=st.text(min_size=1).filter(lambda x: "/" not in x and "@" not in x and ":" not in x),
    db_name=st.text(min_size=1).filter(lambda x: "/" not in x and "?" not in x),
    port=st.text(min_size=1, max_size=5, alphabet="0123456789"),
    scheme=st.sampled_from(["postgresql", "postgres", "postgresql+psycopg2"])
)
def test_get_conn_string_quoting(username, password, hostname, db_name, port, scheme):
    result = get_conn_string(username, password, hostname, db_name, port, scheme=scheme)
    parsed = urlparse(result)
    assert parsed.scheme == scheme
    if parsed.username:
        decoded_username = unquote(parsed.username)
        assert decoded_username == username
    if parsed.password:
        decoded_password = unquote(parsed.password)
        assert decoded_password == password
    assert parsed.hostname == hostname
    assert str(parsed.port) == port
    assert parsed.path.lstrip("/") == db_name
```

**Failing input**: Multiple minimal examples:
- password=":/", hostname="0", db_name="0"
- hostname="[", any other values
- db_name="#", with params

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')
from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse, parse_qs

# Case 1: Password with ":/" breaks URL parsing
result1 = get_conn_string("user", ":/", "localhost", "db", "5432")
try:
    parsed = urlparse(result1)
    port = parsed.port
except ValueError as e:
    print(f"Bug 1: {e}")

# Case 2: Hostname with "[" causes Invalid IPv6 URL
result2 = get_conn_string("user", "pass", "host[name", "db", "5432")
try:
    parsed = urlparse(result2)
except ValueError as e:
    print(f"Bug 2: {e}")

# Case 3: Database name with "#" loses query parameters
result3 = get_conn_string("user", "pass", "localhost", "test#db", "5432", 
                         params={"sslmode": "require"})
parsed = urlparse(result3)
params = parse_qs(parsed.query)
if not params:
    print("Bug 3: Query parameters lost when db_name contains '#'")
```

## Why This Is A Bug

The function creates database connection URLs that are invalid or lose critical configuration data. This violates the basic contract that `get_conn_string` should produce valid, parseable PostgreSQL connection URLs that preserve all input data. Special characters in passwords, hostnames, and database names are legitimate use cases that should be properly handled.

## Fix

```diff
--- a/dagster_postgres/utils.py
+++ b/dagster_postgres/utils.py
@@ -59,9 +59,13 @@ def get_conn_string(
     params: Optional[Mapping[str, object]] = None,
     scheme: str = "postgresql",
 ) -> str:
-    uri = f"{scheme}://{quote(username)}:{quote(password)}@{hostname}:{port}/{db_name}"
+    # Properly quote all components that may contain special characters
+    quoted_hostname = quote(hostname, safe='')
+    quoted_db_name = quote(db_name, safe='')
+    
+    uri = f"{scheme}://{quote(username)}:{quote(password)}@{quoted_hostname}:{port}/{quoted_db_name}"
 
     if params:
         query_string = f"{urlencode(params, quote_via=quote)}"
         uri = f"{uri}?{query_string}"
```