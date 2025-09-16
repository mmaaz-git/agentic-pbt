# Bug Report: troposphere.vpclattice Integer Validator Type Inconsistency

**Target**: `troposphere.vpclattice` (integer validation function)
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `integer` validator function in troposphere accepts non-integer inputs (strings and floats) but doesn't convert them to integers, causing type inconsistencies in CloudFormation templates.

## Property-Based Test

```python
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans()
))
def test_integer_validator_type_consistency(value):
    int_func = vpc.HealthCheckConfig.props['Port'][0]
    
    try:
        result = int_func(value)
        if isinstance(value, str) and value.isdigit():
            assert isinstance(result, int), f"integer validator returned {type(result).__name__} for string '{value}', expected int"
        elif isinstance(value, float):
            assert isinstance(result, int), f"integer validator returned {type(result).__name__} for float {value}, expected int"
    except ValueError:
        pass
```

**Failing input**: `value='0'` (string) and `value=0.0` (float)

## Reproducing the Bug

```python
import troposphere.vpclattice as vpc
import json

hc = vpc.HealthCheckConfig(
    'test',
    Port='8080',
    HealthCheckIntervalSeconds=30.5
)

print(f"Port type: {type(hc.properties['Port'])}")  # <class 'str'>
print(f"Interval type: {type(hc.properties['HealthCheckIntervalSeconds'])}")  # <class 'float'>

json_output = json.dumps(hc.to_dict())
print(json_output)  # {"Port": "8080", "HealthCheckIntervalSeconds": 30.5}
```

## Why This Is A Bug

The `integer` validator function validates that a value CAN be converted to an integer but returns the original value unchanged. This violates the expected behavior of a type validator, which should either:
1. Convert valid inputs to the correct type (integers)
2. Reject invalid inputs with an error

This causes problems because:
- AWS CloudFormation expects integer values for these fields
- Type mismatches can cause deployment failures
- JSON serialization preserves incorrect types

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