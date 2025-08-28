# Bug Report: troposphere.template_generator Numeric Property Names Cause AttributeError

**Target**: `troposphere.template_generator.TemplateGenerator`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

TemplateGenerator crashes with AttributeError when CloudFormation templates contain numeric property names (e.g., "0", "1") in resource Properties.

## Property-Based Test

```python
@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.fixed_dictionaries({
        "Type": aws_resource_types,
        "Properties": st.dictionaries(
            st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
            simple_values,
            min_size=0,
            max_size=5
        )
    }),
    min_size=1,
    max_size=3
))
def test_round_trip_preserves_structure(resources):
    cf_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": resources
    }
    tg_template = tg.TemplateGenerator(cf_template)
    result = tg_template.to_dict()
    assert set(cf_template.keys()) == set(result.keys())
```

**Failing input**: `{'Resources': {'MyBucket': {'Type': 'AWS::S3::Bucket', 'Properties': {'0': 'value'}}}}`

## Reproducing the Bug

```python
import troposphere.template_generator as tg

cf_template = {
    'AWSTemplateFormatVersion': '2010-09-09',
    'Resources': {
        'MyBucket': {
            'Type': 'AWS::S3::Bucket',
            'Properties': {
                '0': 'value'
            }
        }
    }
}

tg_template = tg.TemplateGenerator(cf_template)
```

## Why This Is A Bug

CloudFormation allows numeric strings as property names in JSON/YAML templates. The TemplateGenerator should handle these valid CloudFormation templates without crashing. The error occurs because troposphere tries to set "0" as an attribute on the AWS object, which Python doesn't allow for numeric attribute names.

## Fix

The issue is in the `_create_instance` method when it tries to instantiate troposphere objects with numeric property names. A fix would involve filtering or transforming numeric property names before passing them to the troposphere object constructor:

```diff
--- a/troposphere/template_generator.py
+++ b/troposphere/template_generator.py
@@ -309,7 +309,11 @@ class TemplateGenerator(Template):
             # Create the object
             if issubclass(cls, AWSObject):
                 # AWS Resources
-                return cls(title=ref, **args)
+                # Filter out numeric property names that would cause AttributeError
+                safe_args = {
+                    k: v for k, v in args.items() 
+                    if not (isinstance(k, str) and k.isdigit())
+                }
+                return cls(title=ref, **safe_args)
             elif issubclass(cls, AWSProperty):
                 # AWS Properties
                 return cls(**args)
```