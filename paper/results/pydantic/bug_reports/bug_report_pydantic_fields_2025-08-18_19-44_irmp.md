# Bug Report: pydantic.fields Decimal Constraint Validation Issue

**Target**: `pydantic.fields.Field` with decimal constraints
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Pydantic's Field allows contradictory decimal constraints (decimal_places > max_digits) and incorrectly validates values against these impossible constraints.

## Property-Based Test

```python
from decimal import Decimal
from hypothesis import assume, given, strategies as st
from pydantic import BaseModel, Field, ValidationError

@given(
    max_digits=st.integers(min_value=1, max_value=5),
    decimal_places=st.integers(min_value=1, max_value=10)
)
def test_decimal_places_exceeds_max_digits(max_digits: int, decimal_places: int):
    """Test Field behavior when decimal_places > max_digits."""
    assume(decimal_places > max_digits)
    
    class TestModel(BaseModel):
        value: Decimal = Field(max_digits=max_digits, decimal_places=decimal_places)
    
    test_values = [
        Decimal("0"),
        Decimal("0.0"),
        Decimal("0.00"),
        Decimal("0.01"),
        Decimal("1"),
    ]
    
    any_accepted = False
    for val in test_values:
        try:
            instance = TestModel(value=val)
            any_accepted = True
        except ValidationError:
            pass
    
    assert not any_accepted, f"Field with max_digits={max_digits}, decimal_places={decimal_places} accepted values"
```

**Failing input**: `max_digits=1, decimal_places=2`

## Reproducing the Bug

```python
from decimal import Decimal
from pydantic import BaseModel, Field

class TestModel(BaseModel):
    value: Decimal = Field(max_digits=1, decimal_places=2)

# These values are incorrectly accepted
instance1 = TestModel(value=Decimal("0.0"))
print(f"Accepted: {instance1.value}")

instance2 = TestModel(value=Decimal("0.00"))
print(f"Accepted: {instance2.value}")

instance3 = TestModel(value=Decimal("0.10"))
print(f"Accepted: {instance3.value}")
```

## Why This Is A Bug

The constraint `max_digits=1, decimal_places=2` is mathematically impossible to satisfy:
- `max_digits=1` means the number can have at most 1 total significant digit
- `decimal_places=2` means the number must have exactly 2 digits after the decimal point
- This would require at least 2 digits, making the constraints contradictory

The validation incorrectly accepts values like `Decimal("0.00")` which technically has 2 decimal places but zero significant digits. This creates confusion about what the constraints actually mean and can lead to unexpected validation behavior.

## Fix

The issue should be addressed in one of two ways:

1. **Validation at Field creation**: Raise an error when `decimal_places > max_digits` since this configuration is impossible to satisfy correctly.

2. **Clarify semantics**: If the current behavior is intentional (treating leading zeros specially), the documentation should clearly explain how `max_digits` and `decimal_places` interact, especially for edge cases like zero values.

The first approach is recommended as it prevents users from creating invalid constraint combinations that have undefined behavior.