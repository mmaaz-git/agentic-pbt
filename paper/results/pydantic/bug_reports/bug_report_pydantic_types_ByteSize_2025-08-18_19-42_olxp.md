# Bug Report: pydantic.types.ByteSize Precision Loss in human_readable()

**Target**: `pydantic.types.ByteSize`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

ByteSize.human_readable() method loses significant precision (up to 3%) by aggressively rounding down, making the round-trip conversion non-reversible and causing data loss.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from pydantic import BaseModel
from pydantic.types import ByteSize


@given(st.integers(min_value=1024**3, max_value=10 * 1024**3))
@settings(max_examples=1000)
def test_bytesize_human_readable_precision_loss(value):
    """ByteSize.human_readable() should not lose more than 1% precision"""
    class Model(BaseModel):
        size: ByteSize
    
    m1 = Model(size=value)
    human = m1.size.human_readable()
    m2 = Model(size=human)
    parsed_value = int(m2.size)
    
    if parsed_value != value:
        loss_ratio = abs(value - parsed_value) / value
        assert loss_ratio < 0.01, f"Precision loss of {loss_ratio*100:.2f}% is too high: {value} -> {human} -> {parsed_value}"
```

**Failing input**: `1084587702`

## Reproducing the Bug

```python
from pydantic import BaseModel
from pydantic.types import ByteSize

class Model(BaseModel):
    size: ByteSize

test_value = 1084587702  # ~1.01 GiB
m = Model(size=test_value)

print(f'Original: {test_value} bytes')
print(f'Actual: {test_value / (1024**3):.4f} GiB')
print(f'human_readable(): {m.size.human_readable()}')

m2 = Model(size=m.size.human_readable())
print(f'Parsed back: {int(m2.size)} bytes')
print(f'Data loss: {test_value - int(m2.size)} bytes')
```

## Why This Is A Bug

The human_readable() method is intended to provide a human-friendly representation that can be parsed back. However, it aggressively rounds down, losing up to 3% of the value. For a 1.01 GiB file, it returns "1.0GiB", losing ~10MB of data. This violates the reasonable expectation that a human-readable format should maintain sufficient precision for round-trip conversion.

## Fix

The human_readable() method should include at least one decimal place of precision when the value doesn't align exactly with the unit boundary. For example, 1.01 GiB should return "1.01GiB" or at minimum "1.0GiB" only when the value is very close to exactly 1.0 GiB.

```diff
# In ByteSize.human_readable() method
- return f"{value:.1f}{unit}"  # Current: always one decimal
+ if abs(value - round(value)) < 0.01:
+     return f"{value:.0f}{unit}"  # Whole number when very close
+ else:
+     return f"{value:.2f}{unit}"  # Two decimals for precision
```