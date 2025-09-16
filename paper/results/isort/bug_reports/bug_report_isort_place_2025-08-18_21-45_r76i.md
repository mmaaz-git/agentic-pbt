# Bug Report: isort.place Empty Module Name Handling

**Target**: `isort.place.module` and `isort.place._src_path`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Empty module names incorrectly return 'FIRSTPARTY' instead of the configured default section.

## Property-Based Test

```python
def test_empty_module_name():
    """Test behavior with empty module name."""
    config = Config(default_section="THIRDPARTY")
    result = place.module("", config)
    assert result == config.default_section
```

**Failing input**: Empty string `""`

## Reproducing the Bug

```python
from isort import place
from isort.settings import Config

config = Config(default_section="THIRDPARTY")
result = place.module("", config)
print(f"Result: {result}")  # Returns 'FIRSTPARTY' instead of 'THIRDPARTY'
```

## Why This Is A Bug

When an empty module name is provided, `_src_path` incorrectly identifies it as a first-party module in the current directory. The function should either handle empty strings specially or fall back to the default section. The current behavior violates the expectation that invalid/empty module names would use the default section.

## Fix

```diff
def _src_path(
    name: str,
    config: Config,
    src_paths: Optional[Iterable[Path]] = None,
    prefix: Tuple[str, ...] = (),
) -> Optional[Tuple[str, str]]:
+   if not name:  # Handle empty module name
+       return None
    
    if src_paths is None:
        src_paths = config.src_paths

    root_module_name, *nested_module = name.split(".", 1)
```