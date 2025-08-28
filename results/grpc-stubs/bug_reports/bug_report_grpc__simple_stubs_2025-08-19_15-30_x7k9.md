# Bug Report: grpc._simple_stubs ChannelCache Fails to Reuse Channels

**Target**: `grpc._simple_stubs.ChannelCache`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The ChannelCache in grpc._simple_stubs fails to reuse channels when given identical parameters, creating duplicate channels instead. This defeats the purpose of the cache and causes resource waste.

## Property-Based Test

```python
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: ':' in x),
    st.text(min_size=1, max_size=50),
    st.lists(st.tuples(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=20)), max_size=3),
    st.booleans(),
    st.sampled_from([None, grpc.Compression.NoCompression, grpc.Compression.Gzip]),
)
def test_channel_reuse_property(target, method, options, insecure, compression):
    cache = ChannelCache.get()
    options_tuple = tuple(options)
    
    channel1, _ = cache.get_channel(
        target=target, options=options_tuple,
        channel_credentials=None if insecure else grpc.ssl_channel_credentials(),
        insecure=insecure, compression=compression,
        method=method, _registered_method=False
    )
    
    channel2, _ = cache.get_channel(
        target=target, options=options_tuple,
        channel_credentials=None if insecure else grpc.ssl_channel_credentials(),
        insecure=insecure, compression=compression,
        method=method, _registered_method=False
    )
    
    assert channel1 is channel2  # FAILS: Different channels returned
```

**Failing input**: `target=':', method='0', options=[], insecure=False, compression=None`

## Reproducing the Bug

```python
import grpc
import grpc.experimental
from grpc._simple_stubs import ChannelCache

cache = ChannelCache.get()

target = "localhost:50051"
options = ()
method = "test_method"

# Two calls with identical parameters
channel1, _ = cache.get_channel(
    target=target, options=options,
    channel_credentials=grpc.ssl_channel_credentials(),
    insecure=False, compression=None,
    method=method, _registered_method=False
)

channel2, _ = cache.get_channel(
    target=target, options=options,
    channel_credentials=grpc.ssl_channel_credentials(),
    insecure=False, compression=None,
    method=method, _registered_method=False
)

print(f"Reused channel: {channel1 is channel2}")  # False (BUG!)
print(f"Cache size: {cache._test_only_channel_count()}")  # 2 (should be 1)
```

## Why This Is A Bug

The ChannelCache is designed to reuse channels for identical parameters to save resources. However, it uses credential objects directly in the cache key tuple. Since `grpc.ssl_channel_credentials()` returns a new object each time (even with identical configuration), the cache treats these as different keys and creates duplicate channels. This violates the documented behavior and defeats the cache's purpose.

## Fix

```diff
--- a/grpc/_simple_stubs.py
+++ b/grpc/_simple_stubs.py
@@ -183,9 +183,15 @@ class ChannelCache:
             channel_credentials = (
                 grpc.experimental.insecure_channel_credentials()
             )
         elif channel_credentials is None:
             _LOGGER.debug("Defaulting to SSL channel credentials.")
-            channel_credentials = grpc.ssl_channel_credentials()
-        key = (target, options, channel_credentials, compression)
+            # Use a stable key for default SSL credentials
+            channel_credentials = grpc.ssl_channel_credentials()
+            cred_key = "DEFAULT_SSL"
+        else:
+            # For custom credentials, use object id or a hash of its properties
+            cred_key = id(channel_credentials)
+        
+        key = (target, options, cred_key, compression)
         with self._lock:
             channel_data = self._mapping.get(key, None)
```