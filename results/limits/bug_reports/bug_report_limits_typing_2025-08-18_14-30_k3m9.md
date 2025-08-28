# Bug Report: limits.typing Missing Export in __all__

**Target**: `limits.typing`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `AsyncCoRedisClient` type alias is defined as a public API in limits.typing but is missing from the `__all__` list, making it unavailable through star imports.

## Property-Based Test

```python
def test_all_public_types_in_all():
    """Test that all public type aliases are exported in __all__"""
    import limits.typing
    
    # Get all public attributes (non-underscore)
    public_attrs = {name for name in dir(limits.typing) if not name.startswith('_')}
    
    # Remove special Python attributes
    public_attrs.discard('annotations')
    
    # Check Protocol classes separately (they have non-P aliases)
    protocol_classes = {'RedisClientP', 'AsyncRedisClientP'}
    public_attrs -= protocol_classes
    
    # All remaining public attributes should be in __all__
    all_exports = set(limits.typing.__all__)
    missing = public_attrs - all_exports
    
    assert not missing, f"Public attributes missing from __all__: {missing}"
```

**Failing input**: `AsyncCoRedisClient` is in public attributes but not in `__all__`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

# Direct import works
import limits.typing
assert hasattr(limits.typing, 'AsyncCoRedisClient')

# Star import fails
namespace = {}
exec("from limits.typing import *", namespace)
assert 'AsyncCoRedisClient' not in namespace  # Bug: should be available

print(f"AsyncCoRedisClient defined: {hasattr(limits.typing, 'AsyncCoRedisClient')}")
print(f"AsyncCoRedisClient in __all__: {'AsyncCoRedisClient' in limits.typing.__all__}")
```

## Why This Is A Bug

This violates the Python convention that all public API elements should be included in `__all__`. The `AsyncCoRedisClient` type alias is:
1. Defined without an underscore prefix (indicating public API)
2. Used by other modules in the limits package (limits/aio/storage/redis/coredis.py)
3. A peer to `AsyncRedisClient` which IS in `__all__`

Users relying on star imports (`from limits.typing import *`) will not have access to this type alias, potentially causing import errors and type checking issues.

## Fix

```diff
--- a/limits/typing.py
+++ b/limits/typing.py
@@ -103,6 +103,7 @@ __all__ = [
     "TYPE_CHECKING",
     "Any",
     "AsyncRedisClient",
+    "AsyncCoRedisClient",
     "Awaitable",
     "Callable",
     "ClassVar",
```