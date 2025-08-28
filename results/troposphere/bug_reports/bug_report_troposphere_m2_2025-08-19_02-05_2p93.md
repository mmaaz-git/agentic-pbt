# Bug Report: troposphere.m2 ApplicationVersion Accepts Invalid Negative Values

**Target**: `troposphere.m2.Deployment`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `ApplicationVersion` property in `troposphere.m2.Deployment` accepts negative integers, violating AWS CloudFormation's requirement that application versions must be >= 1.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.m2 as m2

@given(st.integers(min_value=-1000000, max_value=-1))
def test_deployment_negative_application_version(app_version):
    """Test that Deployment ApplicationVersion handles negative integers."""
    deployment = m2.Deployment(
        title="TestDeploy",
        ApplicationId="app-123",
        ApplicationVersion=app_version,
        EnvironmentId="env-456"
    )
    
    serialized = deployment.to_dict()
    props = serialized.get('Properties', {})
    assert props['ApplicationVersion'] == app_version
```

**Failing input**: `-1`

## Reproducing the Bug

```python
import troposphere.m2 as m2

deployment = m2.Deployment(
    title="TestDeploy",
    ApplicationId="app-123",
    ApplicationVersion=-42,
    EnvironmentId="env-456"
)

result = deployment.to_dict()
print(result)
```

## Why This Is A Bug

According to AWS CloudFormation documentation, the ApplicationVersion property must have a minimum value of 1. The troposphere library uses the generic `integer` validator which only checks that the value can be converted to an integer, but doesn't enforce the minimum constraint. This allows invalid CloudFormation templates to be generated that will fail when deployed to AWS.

## Fix

```diff
--- a/troposphere/m2.py
+++ b/troposphere/m2.py
@@ -8,7 +8,7 @@
 
 
 from . import AWSObject, AWSProperty, PropsDictType
-from .validators import boolean, integer
+from .validators import boolean, integer, positive_integer
 
 
 class Definition(AWSProperty):
@@ -48,7 +48,7 @@ class Deployment(AWSObject):
 
     props: PropsDictType = {
         "ApplicationId": (str, True),
-        "ApplicationVersion": (integer, True),
+        "ApplicationVersion": (positive_integer, True),
         "EnvironmentId": (str, True),
     }
```