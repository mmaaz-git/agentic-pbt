# Bug Report: troposphere.validators.integer Type Inconsistency

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `integer` validator function doesn't convert valid numeric strings to integers, returning strings unchanged instead, causing type inconsistency in CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(value=st.one_of(
    st.integers(min_value=-2**31, max_value=2**31-1),
    st.text()
))
def test_integer_validator(value):
    """Integer validator should convert numeric strings to integers"""
    if isinstance(value, int):
        result = integer(value)
        assert result == value
    else:
        try:
            expected = int(value)
            result = integer(value)
            assert result == expected  # FAILS: result is string, not int
        except ValueError:
            with pytest.raises(ValueError):
                integer(value)
```

**Failing input**: `'0'`

## Reproducing the Bug

```python
from troposphere.validators import integer
import troposphere.aps as aps

result = integer('0')
print(f"integer('0') returns: {result!r}")
print(f"Type: {type(result)}")
print(f"Expected: 0 (int), Got: '0' (str)")

filter1 = aps.LoggingFilter(QspThreshold=100)
filter2 = aps.LoggingFilter(QspThreshold='100')
print(f"\nJSON output with integer: {filter1.to_dict()}")
print(f"JSON output with string:  {filter2.to_dict()}")
```

## Why This Is A Bug

The integer validator accepts numeric strings but doesn't convert them to integers, causing CloudFormation templates to contain string values where integers are expected. This violates AWS CloudFormation's type requirements for integer properties.

## Fix

```diff
def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
    try:
-       int(x)
+       return int(x)
    except (ValueError, TypeError):
        raise ValueError("%r is not a valid integer" % x)
-   else:
-       return x
```