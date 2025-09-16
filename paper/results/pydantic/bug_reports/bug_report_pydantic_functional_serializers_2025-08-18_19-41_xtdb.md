# Bug Report: pydantic.functional_serializers Multiple Serializers Not Composing

**Target**: `pydantic.functional_serializers.PlainSerializer` and `pydantic.functional_serializers.WrapSerializer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When multiple `PlainSerializer` or `WrapSerializer` instances are specified in an `Annotated` type, only the last serializer is applied, ignoring all previous ones. This violates the expected composition behavior.

## Property-Based Test

```python
from typing import Annotated
from hypothesis import given, strategies as st
from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

@given(st.integers(), st.integers(min_value=1, max_value=10))
def test_plain_serializer_composition(value, multiplier):
    """Multiple serializers should compose in order."""
    
    def multiply(x):
        return x * multiplier
    
    def add_one(x):
        return x + 1
    
    # Apply two transformations
    TransformedInt = Annotated[int, PlainSerializer(multiply), PlainSerializer(add_one)]
    
    class Model(BaseModel):
        field: TransformedInt
    
    model = Model(field=value)
    result = model.model_dump()
    
    # Property: The transformations should be applied in order
    expected = (value * multiplier) + 1
    assert result['field'] == expected
```

**Failing input**: `value=1, multiplier=2`

## Reproducing the Bug

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer, WrapSerializer

# Test PlainSerializer composition
def double(x):
    return x * 2

def add_ten(x):
    return x + 10

ComposedInt = Annotated[int, PlainSerializer(double), PlainSerializer(add_ten)]

class Model(BaseModel):
    value: ComposedInt

model = Model(value=5)
result = model.model_dump()

# Expected: double(5) = 10, then add_ten(10) = 20
# Actual: 15 (only add_ten is applied)
print(f"Expected: 20, Actual: {result['value']}")  # Prints: Expected: 20, Actual: 15

# Same issue with WrapSerializer
def wrap_double(val, handler, info):
    return handler(val) * 2

def wrap_triple(val, handler, info):
    return handler(val) * 3

ComposedWrap = Annotated[int, WrapSerializer(wrap_double), WrapSerializer(wrap_triple)]

class WrapModel(BaseModel):
    value: ComposedWrap

wrap_model = WrapModel(value=5)
wrap_result = wrap_model.model_dump()

# Expected: 5 * 2 * 3 = 30 (if both applied)
# Actual: 15 (only triple is applied)
print(f"Expected: 30, Actual: {wrap_result['value']}")  # Prints: Expected: 30, Actual: 15
```

## Why This Is A Bug

The Python `typing.Annotated` type is designed to support multiple metadata annotations that should all be considered. When a user specifies multiple serializers, they reasonably expect them to compose - either all applying in sequence or at minimum receiving a clear error that multiple serializers are not supported. Silently ignoring all but the last serializer is unexpected behavior that can lead to subtle bugs in production code.

## Fix

The issue appears to be in how `PlainSerializer` and `WrapSerializer` implement their `__get_pydantic_core_schema__` methods. When multiple serializers are present, each one overwrites the `serialization` field of the schema instead of composing with existing serialization logic.

A high-level fix would involve:
1. Check if a serialization already exists in the schema
2. If it does, compose the new serializer with the existing one
3. Apply serializers in the order they appear in the Annotated type

The fix would need to be implemented in both `/root/hypothesis-llm/envs/pydantic_env/lib/python3.13/site-packages/pydantic/functional_serializers.py` at lines 79-84 (for PlainSerializer) and lines 182-187 (for WrapSerializer) where the serialization is set on the schema.