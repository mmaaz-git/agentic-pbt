# Bug Report: pydantic.main None Defaults Break JSON Round-Trip

**Target**: `pydantic.main.BaseModel` and `pydantic.main.create_model`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Pydantic allows creating models with None as default value for non-optional fields (int, float, str, bool), but these models fail JSON round-trip validation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic import create_model

@given(
    st.sampled_from([int, str, bool, float])
)
def test_create_model_none_default_roundtrip(field_type):
    """Test that models with None defaults can round-trip through JSON."""
    
    # Create model with None default for non-optional type
    DynamicModel = create_model('TestModel', field=(field_type, None))
    
    # This succeeds - model accepts None for non-optional field
    instance = DynamicModel()
    assert instance.field is None
    
    # This fails - JSON round-trip breaks
    json_str = instance.model_dump_json()
    reconstructed = DynamicModel.model_validate_json(json_str)
    assert instance == reconstructed
```

**Failing input**: Any of `int`, `str`, `bool`, `float` types with None default

## Reproducing the Bug

```python
from pydantic import BaseModel, create_model

# Method 1: Using BaseModel directly
class TestModel(BaseModel):
    value: float = None

instance = TestModel()
print(f"Created instance: value={instance.value}")
json_str = instance.model_dump_json() 
print(f"JSON: {json_str}")

# This raises ValidationError
try:
    reconstructed = TestModel.model_validate_json(json_str)
except Exception as e:
    print(f"ERROR: {e}")

# Method 2: Using create_model
DynamicModel = create_model('DynamicModel', value=(float, None))
instance2 = DynamicModel()
print(f"\nDynamic instance: value={instance2.value}")
json_str2 = instance2.model_dump_json()
print(f"JSON: {json_str2}")

# This also raises ValidationError
try:
    reconstructed2 = DynamicModel.model_validate_json(json_str2)
except Exception as e:
    print(f"ERROR: {e}")
```

## Why This Is A Bug

The contract violation occurs because:
1. Pydantic accepts `None` as a default value for non-optional fields during model definition
2. Pydantic successfully creates instances with these None values  
3. Pydantic successfully serializes to JSON with `null` values
4. Pydantic fails to deserialize the same JSON it produced, violating the round-trip property

Either the model should reject None defaults for non-optional fields at definition time, or it should handle the round-trip correctly.

## Fix

The issue could be fixed by either:

1. **Stricter validation at model creation** - Reject None defaults for non-optional types:

```diff
# In model field creation logic
def create_field(field_type, default_value):
+   if default_value is None and not is_optional(field_type):
+       raise ValueError(f"Cannot use None as default for non-optional type {field_type}")
    return FieldInfo(annotation=field_type, default=default_value)
```

2. **Automatic Optional wrapping** - Make fields with None defaults implicitly Optional:

```diff  
# In model field creation logic
def create_field(field_type, default_value):
    if default_value is None and not is_optional(field_type):
+       from typing import Optional
+       field_type = Optional[field_type]
    return FieldInfo(annotation=field_type, default=default_value)
```

3. **Special handling during validation** - Accept None for fields that have None as default during validation, maintaining backwards compatibility.