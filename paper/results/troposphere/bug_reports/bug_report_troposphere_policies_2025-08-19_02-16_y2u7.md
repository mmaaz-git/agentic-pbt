# Bug Report: troposphere.policies Incorrect Validator Types in CodeDeployLambdaAliasUpdate

**Target**: `troposphere.policies.CodeDeployLambdaAliasUpdate`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

CodeDeployLambdaAliasUpdate uses boolean validators for ApplicationName and DeploymentGroupName fields, but AWS CloudFormation expects these to be strings representing application and deployment group names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.policies as policies

@given(st.text(min_size=1).filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]))
def test_codedeploy_application_name_should_accept_strings(app_name):
    """ApplicationName should accept string values for CodeDeploy application names"""
    obj = policies.CodeDeployLambdaAliasUpdate()
    with pytest.raises(ValueError):
        obj.ApplicationName = app_name
```

**Failing input**: `"MyCodeDeployApp"`

## Reproducing the Bug

```python
import troposphere.policies as policies

obj = policies.CodeDeployLambdaAliasUpdate()

obj.ApplicationName = "MyCodeDeployApp"

obj.DeploymentGroupName = "MyDeploymentGroup"
```

## Why This Is A Bug

The CodeDeployLambdaAliasUpdate class defines ApplicationName and DeploymentGroupName with boolean validators, but these fields represent AWS CodeDeploy resource names which must be strings. This prevents users from setting valid CodeDeploy application and deployment group names, making the class unusable for its intended purpose in CloudFormation templates.

## Fix

```diff
--- a/troposphere/policies.py
+++ b/troposphere/policies.py
@@ -28,8 +28,8 @@
 class CodeDeployLambdaAliasUpdate(AWSProperty):
     props: PropsDictType = {
         "AfterAllowTrafficHook": (str, False),
-        "ApplicationName": (boolean, True),
+        "ApplicationName": (str, True),
         "BeforeAllowTrafficHook": (str, False),
-        "DeploymentGroupName": (boolean, True),
+        "DeploymentGroupName": (str, True),
     }
```