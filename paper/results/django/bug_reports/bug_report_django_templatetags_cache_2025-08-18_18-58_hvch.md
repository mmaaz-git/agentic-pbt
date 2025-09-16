# Bug Report: django.templatetags.cache Cache Key Collision

**Target**: `django.templatetags.cache.make_template_fragment_key`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `make_template_fragment_key` function generates identical cache keys for different `vary_on` inputs when one input contains the separator character (colon) used internally by the function.

## Property-Based Test

```python
@given(
    fragment_name=st.text(min_size=1, max_size=20),
    vary_item=st.text(min_size=2, max_size=20).filter(lambda x: ':' in x)
)
def test_cache_key_collision_with_colon(fragment_name, vary_item):
    """Test for collision when using colon separator"""
    parts = vary_item.split(':', 1)
    if len(parts) == 2 and parts[0] and parts[1]:
        vary_on_single = [vary_item]
        vary_on_multi = parts
        
        key_single = cache_module.make_template_fragment_key(fragment_name, vary_on_single)
        key_multi = cache_module.make_template_fragment_key(fragment_name, vary_on_multi)
        
        # Different inputs should produce different keys
        assert key_single != key_multi, f"Collision: {vary_on_single} and {vary_on_multi} produce same key"
```

**Failing input**: `fragment_name="test", vary_item="a:b"`

## Reproducing the Bug

```python
import django
from django.conf import settings

settings.configure(DEBUG=True)
django.setup()

from django.templatetags.cache import make_template_fragment_key

fragment_name = "user_profile"
vary_on_1 = ["user:123"]       # Single string with colon
vary_on_2 = ["user", "123"]    # Two separate strings

key_1 = make_template_fragment_key(fragment_name, vary_on_1)
key_2 = make_template_fragment_key(fragment_name, vary_on_2)

assert key_1 == key_2  # Bug: These should be different!
print(f"Both produce: {key_1}")
```

## Why This Is A Bug

The function uses a colon (`:`) as a separator when hashing the `vary_on` items. This causes a collision where `["a:b"]` produces the same hash as `["a", "b"]` because both result in the byte sequence `b"a:b:"` being fed to the MD5 hasher. This violates the expected property that different inputs should produce different cache keys, potentially causing incorrect cache retrieval in production systems.

## Fix

```diff
def make_template_fragment_key(fragment_name, vary_on=None):
    hasher = md5(usedforsecurity=False)
    if vary_on is not None:
        for arg in vary_on:
-           hasher.update(str(arg).encode())
-           hasher.update(b":")
+           # Include length prefix to prevent collisions
+           arg_bytes = str(arg).encode()
+           hasher.update(len(arg_bytes).to_bytes(4, 'big'))
+           hasher.update(arg_bytes)
    return TEMPLATE_FRAGMENT_KEY_TEMPLATE % (fragment_name, hasher.hexdigest())
```