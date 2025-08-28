# Bug Report: storage3 UnicodeEncodeError with Non-ASCII Headers

**Target**: `storage3.create_client`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `create_client` function crashes with UnicodeEncodeError when headers contain non-ASCII characters, preventing client initialization with certain header values.

## Property-Based Test

```python
@given(
    url=st.one_of(
        st.just("http://localhost:8000"),
        st.just("https://api.example.com"),
        st.text(min_size=1).map(lambda x: f"http://{x}.com")
    ),
    headers=st.dictionaries(st.text(min_size=1), st.text()),
    is_async=st.booleans()
)
def test_create_client_returns_correct_type(url, headers, is_async):
    """Property: create_client returns AsyncStorageClient when is_async=True, SyncStorageClient when False"""
    client = create_client(url, headers, is_async=is_async)
    
    if is_async:
        assert isinstance(client, AsyncStorageClient)
    else:
        assert isinstance(client, SyncStorageClient)
```

**Failing input**: `headers={'\x80': ''}` or `headers={'key': '\x80'}`

## Reproducing the Bug

```python
import storage3

client = storage3.create_client(
    url="http://localhost:8000",
    headers={'\x80': ''},
    is_async=False
)
```

## Why This Is A Bug

HTTP headers must be ASCII-encoded according to RFC 7230. When users accidentally pass non-ASCII characters in headers (e.g., from untrusted input or encoding issues), the library should either:
1. Validate and reject invalid headers with a clear error message
2. Safely encode the headers
3. Strip invalid characters

Instead, it crashes with an unhelpful UnicodeEncodeError from the underlying httpx library, making it difficult to debug.

## Fix

The issue occurs because storage3 passes headers directly to httpx without validation. A fix would validate headers before passing them to the HTTP client:

```diff
--- a/storage3/_sync/client.py
+++ b/storage3/_sync/client.py
@@ -29,9 +29,17 @@ class SyncStorageClient(SyncStorageBucketAPI):
         http_client: Optional[Client] = None,
     ) -> None:
+        # Validate headers contain only ASCII characters
+        for key, value in headers.items():
+            try:
+                key.encode('ascii')
+                value.encode('ascii')
+            except UnicodeEncodeError:
+                raise ValueError(f"Headers must contain only ASCII characters. Invalid header: {key!r}: {value!r}")
+        
         headers = {
             "User-Agent": f"supabase-py/storage3 v{__version__}",
             **headers,
         }
```

The same validation should be added to the AsyncStorageClient class.