# Bug Report: troposphere.template_generator Empty Parameters and Outputs Not Preserved

**Target**: `troposphere.template_generator.TemplateGenerator`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

TemplateGenerator fails to preserve empty Parameters and Outputs sections when converting CloudFormation templates, violating round-trip conversion expectations.

## Property-Based Test

```python
@given(cf_templates)
def test_round_trip_preserves_structure(cf_template):
    tg_template = tg.TemplateGenerator(cf_template)
    result = tg_template.to_dict()
    
    assert set(cf_template.keys()) == set(result.keys()), \
        f"Keys mismatch: {set(cf_template.keys())} != {set(result.keys())}"
```

**Failing input**: `{'AWSTemplateFormatVersion': '2010-09-09', 'Resources': {'MyBucket': {'Type': 'AWS::S3::Bucket', 'Properties': {}}}, 'Parameters': {}, 'Outputs': {}}`

## Reproducing the Bug

```python
import troposphere.template_generator as tg

cf_template = {
    'AWSTemplateFormatVersion': '2010-09-09',
    'Resources': {
        'MyBucket': {
            'Type': 'AWS::S3::Bucket',
            'Properties': {}
        }
    },
    'Parameters': {},
    'Outputs': {}
}

tg_template = tg.TemplateGenerator(cf_template)
result = tg_template.to_dict()

print('Original keys:', sorted(cf_template.keys()))
print('Result keys:', sorted(result.keys()))
print('Parameters preserved:', 'Parameters' in result)
print('Outputs preserved:', 'Outputs' in result)
```

## Why This Is A Bug

CloudFormation templates can have empty Parameters and Outputs sections as placeholders or for template structure consistency. When converting a CloudFormation template to Troposphere and back, these empty sections should be preserved to maintain template structure fidelity. The current behavior breaks round-trip conversion guarantees and may cause issues in workflows that expect template structure preservation.

## Fix

The issue is in the parent Template class's `to_dict()` method which only includes non-empty sections. The fix would preserve empty sections that were explicitly present in the original template:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -900,10 +900,10 @@ class Template:
         if self.conditions:
             t["Conditions"] = self.conditions
         if self.mappings:
             t["Mappings"] = self.mappings
-        if self.outputs:
+        if self.outputs is not None:
             t["Outputs"] = self.outputs
-        if self.parameters:
+        if self.parameters is not None:
             t["Parameters"] = self.parameters
         if self.resources:
             t["Resources"] = self.resources
         if self.rules:
```