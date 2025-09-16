# Bug Report: troposphere.validators Integer Validator Accepts Non-Integer Floats

**Target**: `troposphere.validators.integer`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `integer()` validator in troposphere accepts float values and passes them through unchanged, violating the contract of an integer validator and producing invalid CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import validators

@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_integer_validator_accepts_floats(value):
    """The integer validator should reject non-integer floats but it accepts them."""
    if value != int(value):  # Only test non-integer floats
        try:
            result = validators.integer(value)
            int_result = int(result)  
            assert False, f"integer() accepted float {value} and converted to {int_result}"
        except (ValueError, TypeError):
            pass
```

**Failing input**: `1.5`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators, Template
import troposphere.appmesh as appmesh
import json

# Bug: integer validator accepts floats
result = validators.integer(1.5)
print(f"validators.integer(1.5) = {result}")  # Output: 1.5

# This creates invalid CloudFormation templates
t = Template()
node = appmesh.VirtualNode(
    'TestNode',
    MeshName='test-mesh',
    Spec=appmesh.VirtualNodeSpec(
        Listeners=[
            appmesh.Listener(
                PortMapping=appmesh.PortMapping(
                    Port=8080.5,  # Float port number!
                    Protocol='http'
                )
            )
        ]
    )
)
t.add_resource(node)

# The generated template contains invalid float port
template_json = json.loads(t.to_json())
port = template_json['Resources']['TestNode']['Properties']['Spec']['Listeners'][0]['PortMapping']['Port']
print(f"Port in generated template: {port}")  # Output: 8080.5 (invalid!)
```

## Why This Is A Bug

The `integer()` validator is used throughout troposphere to validate integer-typed CloudFormation properties like port numbers, counts, and timeouts. By accepting float values, it:

1. Violates its contract as an "integer" validator
2. Produces CloudFormation templates with float values where AWS expects integers
3. Can cause deployment failures when AWS CloudFormation rejects the invalid templates
4. Silently truncates decimal values when converted with `int()`, potentially causing unexpected behavior

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,8 +45,10 @@
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
-    except (ValueError, TypeError):
+        int_val = int(x)
+        # Reject floats that aren't exact integers
+        if isinstance(x, float) and x != int_val:
+            raise ValueError("%r is not a valid integer" % x)
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```