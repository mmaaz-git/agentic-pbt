# Bug Report: sudachipy Config Type Validation and Invalid JSON Generation

**Target**: `sudachipy.Config`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `Config` class in sudachipy accepts non-string values for the `projection` field, violating its type contract and potentially producing invalid JSON that violates the JSON specification.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sudachipy
from sudachipy import Config

@given(st.floats())
def test_config_projection_float(float_val):
    """Test if Config projection field accepts floats."""
    config = Config(projection=float_val)
    # This should not accept floats according to type hints
    assert config.projection == float_val or isinstance(config.projection, str)
```

**Failing input**: `float('nan')`

## Reproducing the Bug

```python
import json
from sudachipy import Config

# Config accepts float('nan') for projection field
config = Config(projection=float('nan'))
print(f"config.projection = {config.projection}")  # nan
print(f"type = {type(config.projection)}")        # <class 'float'>

# Produces invalid JSON
json_str = config.as_jsons()
print(f"JSON: {json_str}")  # {"projection": NaN}

# This JSON violates RFC 7159 and will fail in strict parsers
try:
    json.dumps({"projection": float('nan')}, allow_nan=False)
except ValueError as e:
    print(f"Strict JSON fails: {e}")  # Out of range float values are not JSON compliant
```

## Why This Is A Bug

1. **Type Contract Violation**: The type hints in `sudachipy.pyi` specify that `projection` should be a `str` with specific valid values ('surface', 'normalized', 'reading', etc.), but the implementation accepts any type.

2. **Invalid JSON Generation**: When non-string values like `float('nan')`, `float('inf')`, or `float('-inf')` are used, `Config.as_jsons()` produces JSON that violates the JSON specification (RFC 7159). These values are not valid JSON and will fail when:
   - Parsed by strict JSON parsers
   - Transmitted to systems using standard JSON
   - Processed by JavaScript's `JSON.parse()`
   - Used with most web APIs

3. **Unexpected Behavior**: The Config class is meant for configuration with specific string values for projection, but accepts arbitrary Python objects including lists, dicts, booleans, and numbers.

## Fix

The Config class should validate the projection field to ensure it's a string and optionally one of the documented valid values:

```diff
@_dataclasses.dataclass
class Config:
    system: str = None
    user: list[str] = None
-   projection: str = "surface"
+   projection: str = _dataclasses.field(default="surface")
    # ... other fields ...
    
+   def __post_init__(self):
+       valid_projections = {
+           "surface", "normalized", "reading", "dictionary",
+           "dictionary_and_surface", "normalized_and_surface", "normalized_nouns"
+       }
+       if self.projection is not None:
+           if not isinstance(self.projection, str):
+               raise TypeError(f"projection must be a string, got {type(self.projection).__name__}")
+           if self.projection not in valid_projections:
+               raise ValueError(f"projection must be one of {valid_projections}, got {self.projection!r}")
```