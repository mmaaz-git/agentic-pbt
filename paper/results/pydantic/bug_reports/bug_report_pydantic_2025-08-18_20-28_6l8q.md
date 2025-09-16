# Bug Report: Pydantic JSON Round-Trip Fails for Special Float Values

**Target**: `pydantic.BaseModel.model_dump_json` and `model_validate_json`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Pydantic's JSON serialization violates the round-trip property for special float values (infinity, negative infinity, and NaN). These values are serialized as `null` which cannot be deserialized back to the original float values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic import BaseModel
import math

@given(
    special_float=st.sampled_from([float('inf'), float('-inf'), float('nan')])
)
def test_special_float_json_roundtrip(special_float):
    class FloatModel(BaseModel):
        value: float
    
    original = FloatModel(value=special_float)
    json_str = original.model_dump_json()
    restored = FloatModel.model_validate_json(json_str)
    
    if math.isnan(special_float):
        assert math.isnan(restored.value)
    else:
        assert restored.value == special_float
```

**Failing input**: `float('inf')`, `float('-inf')`, or `float('nan')`

## Reproducing the Bug

```python
from pydantic import BaseModel

class FloatModel(BaseModel):
    value: float

model = FloatModel(value=float('inf'))
print(f"Original value: {model.value}")

json_str = model.model_dump_json()
print(f"JSON representation: {json_str}")

try:
    restored = FloatModel.model_validate_json(json_str)
    print(f"Restored value: {restored.value}")
except Exception as e:
    print(f"ERROR: {e}")
```

## Why This Is A Bug

This violates the fundamental round-trip property that `model_validate_json(model_dump_json(x))` should equal `x`. The JSON serialization loses information by converting special float values to `null`, making it impossible to reconstruct the original model. This is particularly problematic because:

1. The dict round-trip (`model_validate(model_dump(x))`) works correctly and preserves these values
2. Python's standard `json` module handles these values correctly using JavaScript literals (`Infinity`, `-Infinity`, `NaN`)
3. The underlying `pydantic_core.to_json` function supports proper serialization via the `inf_nan_mode` parameter

## Fix

The issue can be fixed by exposing the `inf_nan_mode` parameter in `model_dump_json()` or changing the default behavior. Here's a high-level approach:

```diff
# In pydantic's model_dump_json method
def model_dump_json(
    self,
    *,
    indent: int | None = None,
+   inf_nan_mode: str = 'constants',  # or 'null' for backward compatibility
    ...
) -> str:
    # Pass inf_nan_mode to the underlying serialization
-   return pydantic_core.to_json(self.model_dump(...))
+   return pydantic_core.to_json(self.model_dump(...), inf_nan_mode=inf_nan_mode)
```

Alternatively, use `inf_nan_mode='constants'` by default to match Python's json module behavior and preserve the round-trip property.