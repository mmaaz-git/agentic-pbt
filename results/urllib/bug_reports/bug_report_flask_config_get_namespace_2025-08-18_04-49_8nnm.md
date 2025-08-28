# Bug Report: Flask Config.get_namespace Key Collision Due to Case Folding

**Target**: `flask.Config.get_namespace`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Flask's `Config.get_namespace()` method with `lowercase=True` (the default) causes silent data loss when configuration keys with the same prefix differ only in case, as it collapses them into a single lowercase key.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from flask import Config
import string

@given(
    base_key=st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
    prefix=st.text(min_size=1, max_size=5, alphabet=string.ascii_uppercase),
    values=st.lists(st.text(), min_size=2, max_size=5)
)
def test_config_namespace_key_collision_bug(base_key, prefix, values):
    if len(values) < 2:
        return
    
    config = Config('.')
    
    key1 = f"{prefix}_{base_key.upper()}"
    key2 = f"{prefix}_{base_key.lower()}"
    
    if key1 == key2:
        return
    
    config[key1] = values[0]
    config[key2] = values[1]
    
    assert key1 in config
    assert key2 in config
    
    namespace = config.get_namespace(f"{prefix}_")
    
    expected_keys = 2
    actual_keys = len(namespace)
    
    assert actual_keys == expected_keys
```

**Failing input**: `test_config_namespace_key_collision_bug(base_key='a', prefix='A', values=['', ''])`

## Reproducing the Bug

```python
from flask import Config

config = Config('.')

config['API_KeyName'] = 'value1'  
config['API_KEYNAME'] = 'value2'
config['API_keyname'] = 'value3'

namespace = config.get_namespace('API_')

print(f"Config keys: {[k for k in config if k.startswith('API_')]}")
print(f"Namespace result: {dict(namespace)}")

assert len(namespace) == 3, f"Expected 3 keys, got {len(namespace)}"
```

## Why This Is A Bug

The `get_namespace()` method is designed to extract configuration subsets for passing to functions or constructors. When multiple configuration keys exist that differ only in case (e.g., from different configuration sources or naming conventions), the method silently loses all but one value instead of preserving them or raising an error. This violates the principle that configuration data should not be silently discarded, especially since Flask Config explicitly supports case-sensitive keys.

## Fix

```diff
--- a/flask/config.py
+++ b/flask/config.py
@@ -246,10 +246,16 @@ class Config(dict):
                           dictionary should not include the namespace
         """
         rv = {}
         for k, v in self.items():
             if not k.startswith(namespace):
                 continue
             if trim_namespace:
                 key = k[len(namespace) :]
             else:
                 key = k
             if lowercase:
                 key = key.lower()
+                if key in rv:
+                    import warnings
+                    warnings.warn(
+                        f"Config key collision in get_namespace(): '{k}' overwrites previous key when lowercased to '{key}'",
+                        RuntimeWarning,
+                        stacklevel=2
+                    )
             rv[key] = v
         return rv
```