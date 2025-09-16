# Bug Report: pydantic.v1 Decimal Precision Loss in JSON Serialization

**Target**: `pydantic.v1.BaseModel` with `Decimal` fields
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

High-precision Decimal values lose precision when serialized to JSON and deserialized back, violating the round-trip property and potentially causing data corruption.

## Property-Based Test

```python
from decimal import Decimal
from fractions import Fraction
import pydantic.v1
from hypothesis import given, strategies as st


def fraction_to_decimal(frac):
    return Decimal(str(frac.numerator)) / Decimal(str(frac.denominator))


@given(
    decimal_val=st.decimals(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_decimal_json_roundtrip(decimal_val):
    class DecimalModel(pydantic.v1.BaseModel):
        value: Decimal
    
    original = DecimalModel(value=decimal_val)
    json_str = original.json()
    reconstructed = DecimalModel.parse_raw(json_str)
    
    assert original.value == reconstructed.value
```

**Failing input**: `Decimal('99503980.42126126126126126126')`

## Reproducing the Bug

```python
from decimal import Decimal
import pydantic.v1


class DecimalModel(pydantic.v1.BaseModel):
    value: Decimal


original_value = Decimal('99503980.42126126126126126126')
model = DecimalModel(value=original_value)

json_str = model.json()
reconstructed = DecimalModel.parse_raw(json_str)

print(f"Original:      {model.value}")
print(f"Reconstructed: {reconstructed.value}")
print(f"Equal:         {model.value == reconstructed.value}")
print(f"Difference:    {abs(model.value - reconstructed.value)}")
```

## Why This Is A Bug

Pydantic's JSON serialization converts Decimal to float internally, which causes precision loss for high-precision decimals. This violates the expected round-trip property where `parse_raw(model.json())` should reconstruct the exact same model. For financial or scientific applications requiring exact decimal arithmetic, this silent precision loss could lead to data corruption.

The issue occurs because the default JSON encoder converts Decimal to float:
- Original: `Decimal('99503980.42126126126126126126')` (20 decimal places)
- After float conversion: `99503980.42126127` (8 decimal places)
- Precision lost: ~8.74e-9

## Fix

Configure the model to serialize Decimals as strings to preserve precision:

```diff
class DecimalModel(pydantic.v1.BaseModel):
    value: Decimal
+   
+   class Config:
+       json_encoders = {
+           Decimal: str
+       }
```

Alternatively, pydantic could default to string serialization for Decimals or provide a global configuration option to preserve decimal precision.