# Bug Report: troposphere.Parameter Accepts Invalid CloudFormation Types

**Target**: `troposphere.Parameter`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The Parameter class in troposphere accepts invalid Type values without validation, allowing creation of CloudFormation templates that AWS will reject.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import Template, Parameter
import json

VALID_TYPES = {'String', 'Number', 'List<Number>', 'CommaDelimitedList'}

@given(st.text().filter(lambda s: s not in VALID_TYPES))
def test_parameter_accepts_invalid_types(invalid_type):
    p = Parameter('TestParam', Type=invalid_type)
    t = Template()
    t.add_parameter(p)
    json_str = t.to_json()
    parsed = json.loads(json_str)
    assert parsed['Parameters']['TestParam']['Type'] == invalid_type
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
from troposphere import Template, Parameter
import json

p = Parameter('MyParam', Type='')
t = Template()
t.add_parameter(p)

print(t.to_json())
```

Output:
```json
{
 "Parameters": {
  "MyParam": {
   "Type": ""
  }
 },
 "Resources": {}
}
```

## Why This Is A Bug

CloudFormation requires Parameter Type to be one of: `String`, `Number`, `List<Number>`, `CommaDelimitedList`, or specific AWS parameter types like `AWS::EC2::Instance::Id`. An empty string or arbitrary text like "Boolean" or "Integer" are invalid and will cause CloudFormation stack creation/update to fail. The library should validate these values to prevent generating invalid templates.

## Fix

Add validation to the Parameter class to check Type against valid CloudFormation parameter types:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -450,10 +450,25 @@ class Parameter(AWSDeclaration):
         "NoEcho": (bool, False),
         "Type": (str, True),
     }
+    
+    VALID_TYPES = {
+        'String', 'Number', 'List<Number>', 'CommaDelimitedList',
+        'AWS::EC2::AvailabilityZone::Name', 'AWS::EC2::Image::Id',
+        # ... other AWS types
+    }
 
     def __init__(self, title, **kwargs):
         super().__init__(title, **kwargs)
         self.depends_on = []
+        self.validate_type()
+    
+    def validate_type(self):
+        param_type = self.properties.get('Type')
+        if param_type and not param_type.startswith('AWS::') and not param_type.startswith('List<AWS::'):
+            if param_type not in self.VALID_TYPES:
+                raise ValueError(
+                    f"Invalid Parameter Type '{param_type}'. Must be one of: {', '.join(sorted(self.VALID_TYPES))}"
+                )
```