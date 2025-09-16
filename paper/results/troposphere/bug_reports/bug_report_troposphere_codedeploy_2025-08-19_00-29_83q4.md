# Bug Report: troposphere.codedeploy DeploymentGroup Validation Failure

**Target**: `troposphere.codedeploy.DeploymentGroup`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

DeploymentGroup's validate() method fails to enforce mutually exclusive constraints due to a case mismatch between property names and validator expectations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere import codedeploy

@given(
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_deployment_group_mutually_exclusive(has_ec2_filters, has_ec2_set, has_on_prem_filters, has_on_prem_set):
    """DeploymentGroup should enforce mutual exclusivity constraints."""
    kwargs = {
        "ApplicationName": "TestApp",
        "ServiceRoleArn": "arn:aws:iam::123456789012:role/CodeDeployRole"
    }
    
    if has_ec2_filters:
        kwargs["Ec2TagFilters"] = [codedeploy.Ec2TagFilters(Key="Name", Value="Test")]
    if has_ec2_set:
        kwargs["Ec2TagSet"] = codedeploy.Ec2TagSet()
    if has_on_prem_filters:
        kwargs["OnPremisesInstanceTagFilters"] = [codedeploy.OnPremisesInstanceTagFilters(Key="Name", Value="Test")]
    if has_on_prem_set:
        kwargs["OnPremisesTagSet"] = codedeploy.OnPremisesTagSet()
    
    dg = codedeploy.DeploymentGroup("TestDG", **kwargs)
    
    should_fail = (has_ec2_filters and has_ec2_set) or (has_on_prem_filters and has_on_prem_set)
    
    if should_fail:
        with pytest.raises(ValueError, match="only one of the following can be specified"):
            dg.validate()
    else:
        dg.validate()
```

**Failing input**: `has_ec2_filters=True, has_ec2_set=True, has_on_prem_filters=False, has_on_prem_set=False`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import codedeploy

dg = codedeploy.DeploymentGroup(
    "TestDG",
    ApplicationName="TestApp",
    ServiceRoleArn="arn:aws:iam::123456789012:role/CodeDeployRole",
    Ec2TagFilters=[codedeploy.Ec2TagFilters(Key="Name", Value="Test")],
    Ec2TagSet=codedeploy.Ec2TagSet()
)

dg.validate()
print("ERROR: validate() did not raise - mutually exclusive constraint violated!")
```

## Why This Is A Bug

The DeploymentGroup class defines mutually exclusive properties (Ec2TagFilters vs Ec2TagSet, OnPremisesInstanceTagFilters vs OnPremisesTagSet). The validate_deployment_group function checks for "EC2TagFilters" but the actual property name is "Ec2TagFilters" (note the case difference). This case mismatch causes the validation to fail silently, allowing invalid configurations.

## Fix

```diff
--- a/troposphere/validators/codedeploy.py
+++ b/troposphere/validators/codedeploy.py
@@ -47,8 +47,8 @@ def validate_deployment_group(self):
     """
     Class: DeploymentGroup
     """
-    ec2_conds = ["EC2TagFilters", "Ec2TagSet"]
-    onPremises_conds = ["OnPremisesInstanceTagFilters", "OnPremisesTagSet"]
+    ec2_conds = ["Ec2TagFilters", "Ec2TagSet"]
+    onPremises_conds = ["OnPremisesInstanceTagFilters", "OnPremisesTagSet"]
     mutually_exclusive(self.__class__.__name__, self.properties, ec2_conds)
     mutually_exclusive(self.__class__.__name__, self.properties, onPremises_conds)
```