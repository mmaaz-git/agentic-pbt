# Bug Report: troposphere.constants Missing M5A and M5AD Instance Types

**Target**: `troposphere.constants`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The troposphere.constants module is missing four EC2 instance type constants that are supported by AWS: M5A_8XLARGE, M5A_16XLARGE, M5AD_8XLARGE, and M5AD_16XLARGE.

## Property-Based Test

```python
def test_m5a_instance_completeness():
    """Test that M5A instance family has all AWS-supported sizes."""
    
    expected_m5a_instances = {
        'M5A_LARGE': 'm5a.large',
        'M5A_XLARGE': 'm5a.xlarge', 
        'M5A_2XLARGE': 'm5a.2xlarge',
        'M5A_4XLARGE': 'm5a.4xlarge',
        'M5A_8XLARGE': 'm5a.8xlarge',      # MISSING!
        'M5A_12XLARGE': 'm5a.12xlarge',
        'M5A_16XLARGE': 'm5a.16xlarge',    # MISSING!
        'M5A_24XLARGE': 'm5a.24xlarge'
    }
    
    missing = []
    for const_name, expected_value in expected_m5a_instances.items():
        if hasattr(tc, const_name):
            actual = getattr(tc, const_name)
            assert actual == expected_value
        else:
            missing.append((const_name, expected_value))
    
    assert len(missing) == 0, f"Missing M5A constants: {missing}"
```

**Failing input**: Test fails due to missing constants, not specific input values

## Reproducing the Bug

```python
import troposphere.constants as tc

# These constants should exist but don't
try:
    print(tc.M5A_8XLARGE)
except AttributeError:
    print("ERROR: M5A_8XLARGE constant is missing")

try:
    print(tc.M5A_16XLARGE)
except AttributeError:
    print("ERROR: M5A_16XLARGE constant is missing")

try:
    print(tc.M5AD_8XLARGE)
except AttributeError:
    print("ERROR: M5AD_8XLARGE constant is missing")
    
try:
    print(tc.M5AD_16XLARGE)
except AttributeError:
    print("ERROR: M5AD_16XLARGE constant is missing")

# These instance types are supported by AWS
# Source: https://aws.amazon.com/ec2/instance-types/m5/
print("\nAWS supports these instance types that are missing from troposphere:")
print("- m5a.8xlarge")
print("- m5a.16xlarge")
print("- m5ad.8xlarge")
print("- m5ad.16xlarge")
```

## Why This Is A Bug

The troposphere library aims to provide constants for all AWS CloudFormation resources. The M5A and M5AD instance families are missing the 8xlarge and 16xlarge sizes that AWS actually supports. This means users cannot use these constants when creating CloudFormation templates with troposphere, forcing them to use string literals instead, which defeats the purpose of having constants.

## Fix

```diff
--- a/troposphere/constants.py
+++ b/troposphere/constants.py
@@ -317,7 +317,9 @@ M5A_LARGE: Final = "m5a.large"
 M5A_XLARGE: Final = "m5a.xlarge"
 M5A_2XLARGE: Final = "m5a.2xlarge"
 M5A_4XLARGE: Final = "m5a.4xlarge"
+M5A_8XLARGE: Final = "m5a.8xlarge"
 M5A_12XLARGE: Final = "m5a.12xlarge"
+M5A_16XLARGE: Final = "m5a.16xlarge"
 M5A_24XLARGE: Final = "m5a.24xlarge"
 
 M5AD_LARGE: Final = "m5ad.large"
@@ -325,6 +327,8 @@ M5AD_XLARGE: Final = "m5ad.xlarge"
 M5AD_2XLARGE: Final = "m5ad.2xlarge"
 M5AD_4XLARGE: Final = "m5ad.4xlarge"
+M5AD_8XLARGE: Final = "m5ad.8xlarge"
 M5AD_12XLARGE: Final = "m5ad.12xlarge"
+M5AD_16XLARGE: Final = "m5ad.16xlarge"
 M5AD_24XLARGE: Final = "m5ad.24xlarge"
```