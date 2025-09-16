# Bug Report: isort.place None Config Handling

**Target**: `isort.place.module` and `isort.place.module_with_reason`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Passing None as the config parameter causes an AttributeError instead of using the DEFAULT_CONFIG as suggested by the function signature.

## Property-Based Test

```python
def test_none_config():
    """Test that None config falls back to DEFAULT_CONFIG."""
    result1 = place.module("test.module")
    result2 = place.module("test.module", None)
    assert result1 == result2
```

**Failing input**: `place.module("test.module", None)`

## Reproducing the Bug

```python
from isort import place

try:
    result = place.module("test.module", None)
except AttributeError as e:
    print(f"Error: {e}")  # AttributeError: 'NoneType' object has no attribute 'forced_separate'
```

## Why This Is A Bug

The function signature suggests that config has a default value (DEFAULT_CONFIG), but when None is explicitly passed, the function doesn't handle it properly. This violates the API contract where None should either be rejected with a clear error or treated as "use the default".

## Fix

```diff
def module(name: str, config: Config = DEFAULT_CONFIG) -> str:
    """Returns the section placement for the given module name."""
+   if config is None:
+       config = DEFAULT_CONFIG
    return module_with_reason(name, config)[0]


@lru_cache(maxsize=1000)
def module_with_reason(name: str, config: Config = DEFAULT_CONFIG) -> Tuple[str, str]:
    """Returns the section placement for the given module name alongside the reasoning."""
+   if config is None:
+       config = DEFAULT_CONFIG
    return (
        _forced_separate(name, config)
        or _local(name, config)
        or _known_pattern(name, config)
        or _src_path(name, config)
        or (config.default_section, "Default option in Config or universal default.")
    )
```