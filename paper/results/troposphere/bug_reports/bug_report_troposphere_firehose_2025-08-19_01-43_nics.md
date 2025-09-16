# Bug Report: troposphere.firehose Naming Convention Violation

**Target**: `troposphere.firehose.IcebergDestinationConfiguration`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `IcebergDestinationConfiguration` class has a property named `s3BackupMode` with lowercase 's', violating AWS CloudFormation naming conventions where all other similar classes use `S3BackupMode` with uppercase 'S'.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(st.just(None))
def test_property_naming_conventions(dummy):
    """Property names should follow AWS CloudFormation conventions (PascalCase)."""
    for name, obj in inspect.getmembers(firehose):
        if inspect.isclass(obj) and issubclass(obj, AWSProperty) and obj != AWSProperty:
            if hasattr(obj, 'props'):
                for prop_name in obj.props.keys():
                    if prop_name:
                        first_char = prop_name[0]
                        assert first_char.isupper() or not first_char.isalpha(), f"{name}.{prop_name} should start with uppercase"
```

**Failing input**: Testing `IcebergDestinationConfiguration` class properties

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import firehose

iceberg = firehose.IcebergDestinationConfiguration()
assert 's3BackupMode' in iceberg.props

other_classes = [
    firehose.ExtendedS3DestinationConfiguration(),
    firehose.ElasticsearchDestinationConfiguration(),
    firehose.SnowflakeDestinationConfiguration(),
    firehose.SplunkDestinationConfiguration(),
]

for obj in other_classes:
    if 'S3BackupMode' in obj.props:
        assert 'S3BackupMode' in obj.props
        assert 's3BackupMode' not in obj.props

print("Bug: IcebergDestinationConfiguration uses 's3BackupMode' (lowercase)")
print("All other classes use 'S3BackupMode' (uppercase)")
```

## Why This Is A Bug

This violates AWS CloudFormation naming conventions where service acronyms like "S3" should always be uppercase in property names. All other destination configuration classes in the same module correctly use `S3BackupMode` with uppercase 'S'. This inconsistency could lead to CloudFormation template generation errors or confusion for users expecting consistent naming.

## Fix

```diff
--- a/troposphere/firehose.py
+++ b/troposphere/firehose.py
@@ -630,7 +630,7 @@ class IcebergDestinationConfiguration(AWSProperty):
         "RetryOptions": (RetryOptions, False),
         "RoleARN": (str, True),
         "S3Configuration": (S3DestinationConfiguration, True),
-        "s3BackupMode": (str, False),
+        "S3BackupMode": (str, False),
     }
```