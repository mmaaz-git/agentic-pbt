# Bug Report: troposphere.validators Integer Validator Accepts Floats Without Conversion

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer` validator in troposphere accepts float values but returns them unchanged as floats, violating the expected contract that integer-typed properties should contain integer values.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.networkfirewall import PortRange

@given(
    from_port=st.one_of(st.integers(), st.floats()),
    to_port=st.one_of(st.integers(), st.floats())
)
def test_portrange_integer_validation(from_port, to_port):
    """Test that PortRange stores integer values for ports"""
    port_range = PortRange(FromPort=from_port, ToPort=to_port)
    # Properties defined as integer should store integers
    assert isinstance(port_range.properties['FromPort'], int)
    assert isinstance(port_range.properties['ToPort'], int)
```

**Failing input**: `from_port=0.0, to_port=0`

## Reproducing the Bug

```python
from troposphere.networkfirewall import PortRange
from troposphere.validators import integer

# Bug 1: PortRange accepts floats but stores them as floats
port_range = PortRange(FromPort=80.0, ToPort=443.5)
print(f"FromPort: {port_range.properties['FromPort']} (type: {type(port_range.properties['FromPort'])})")
print(f"ToPort: {port_range.properties['ToPort']} (type: {type(port_range.properties['ToPort'])})")

# Bug 2: The integer validator doesn't convert to int
result = integer(1.5)
print(f"integer(1.5) returns: {result} (type: {type(result)})")
```

## Why This Is A Bug

The `integer` validator is used throughout troposphere to validate integer-typed CloudFormation properties. However, it only checks if a value can be converted to int (`int(x)`) but returns the original value unchanged. This means:

1. Float values like `1.0` or `1.5` pass validation but remain as floats
2. CloudFormation templates generated may contain float values where integers are expected
3. The type contract is violated - properties declared as `integer` store non-integer values

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,10 +46,10 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        result = int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
-        return x
+        return result
```