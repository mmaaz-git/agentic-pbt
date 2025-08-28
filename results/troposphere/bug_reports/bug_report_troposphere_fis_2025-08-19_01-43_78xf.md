# Bug Report: troposphere.fis None Handling for Optional Properties

**Target**: `troposphere.fis`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Optional properties in troposphere.fis AWS resource classes fail to accept None values, causing TypeError exceptions and breaking round-trip dict conversion.

## Property-Based Test

```python
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=0, max_size=50)
)
def test_nested_property_round_trip(bucket_name, prefix):
    """Test round-trip for nested properties"""
    # Create nested structure
    s3_config = fis.ExperimentReportS3Configuration(
        BucketName=bucket_name,
        Prefix=prefix if prefix else None
    )
    outputs = fis.Outputs(ExperimentReportS3Configuration=s3_config)
    report_config = fis.ExperimentTemplateExperimentReportConfiguration(
        Outputs=outputs
    )
    
    # Convert to dict
    dict_repr = report_config.to_dict()
    
    # Recreate from dict
    report_config2 = fis.ExperimentTemplateExperimentReportConfiguration._from_dict(**dict_repr)
    
    # Should be equal
    assert report_config.to_dict() == report_config2.to_dict()
```

**Failing input**: `bucket_name='0', prefix=''`

## Reproducing the Bug

```python
import troposphere.fis as fis

# Bug 1: Cannot set optional property to None
try:
    config = fis.ExperimentReportS3Configuration(
        BucketName="test-bucket",
        Prefix=None  # Optional property
    )
except TypeError as e:
    print(f"Failed: {e}")

# Bug 2: Round-trip with None fails
test_dict = {"BucketName": "test-bucket", "Prefix": None}
try:
    config = fis.ExperimentReportS3Configuration._from_dict(**test_dict)
except TypeError as e:
    print(f"Failed: {e}")
```

## Why This Is A Bug

Optional properties should accept None values to represent absence of the property. This is standard Python behavior and necessary for:
1. Explicit indication that an optional property is not set
2. Round-trip serialization/deserialization of objects with optional properties
3. Compatibility with JSON/dict representations where None values may be present

The current implementation incorrectly validates None against the property's type (e.g., str), causing TypeError for valid use cases.

## Fix

The issue is in BaseAWSObject.__setattr__ method. It needs to allow None for optional properties:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,11 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            required = self.props[name][1]
+            
+            # Allow None for optional properties
+            if not required and value is None:
+                return self.properties.__setitem__(name, value)
 
             # If the value is a AWSHelperFn we can't do much validation
```