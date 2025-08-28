# Bug Report: troposphere.greengrassv2 Missing Documentation Link

**Target**: `troposphere.greengrassv2.IoTJobRateIncreaseCriteria`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-01-19

## Summary

The `IoTJobRateIncreaseCriteria` class is missing its AWS CloudFormation documentation link, breaking consistency with all other AWSProperty classes in the module.

## Property-Based Test

```python
import troposphere.greengrassv2 as ggv2

# Check all AWSProperty classes for documentation consistency
aws_property_classes = [
    ggv2.ComponentDependencyRequirement,
    ggv2.ComponentPlatform,
    ggv2.LambdaEventSource,
    ggv2.IoTJobRateIncreaseCriteria,  # This one is missing documentation
    ggv2.IoTJobExponentialRolloutRate,
]

for cls in aws_property_classes:
    has_aws_docs = cls.__doc__ and "http://docs.aws.amazon.com" in (cls.__doc__ or "")
    if not has_aws_docs:
        print(f"Missing AWS documentation: {cls.__name__}")
```

**Failing input**: `IoTJobRateIncreaseCriteria` class definition

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.greengrassv2 as ggv2

# IoTJobRateIncreaseCriteria is missing its docstring
print("IoTJobRateIncreaseCriteria docstring:", ggv2.IoTJobRateIncreaseCriteria.__doc__)
# Output: None

# Compare with other classes that have proper documentation
print("IoTJobExponentialRolloutRate has docs:", 
      "http://docs.aws.amazon.com" in (ggv2.IoTJobExponentialRolloutRate.__doc__ or ""))
# Output: True
```

## Why This Is A Bug

All other AWSProperty classes in the module include AWS CloudFormation documentation links in their docstrings. The `IoTJobRateIncreaseCriteria` class breaks this pattern, which could indicate:
1. Missing documentation during code generation
2. An undocumented internal AWS property
3. A code generation oversight

This inconsistency makes it harder for users to find official AWS documentation for this property.

## Fix

```diff
--- a/troposphere/greengrassv2.py
+++ b/troposphere/greengrassv2.py
@@ -211,6 +211,10 @@ class IoTJobAbortConfig(AWSProperty):
 
 
 class IoTJobRateIncreaseCriteria(AWSProperty):
+    """
+    `IoTJobRateIncreaseCriteria <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-greengrassv2-deployment-iotjobrateincreasecriteria.html>`__
+    """
+
     props: PropsDictType = {
         "NumberOfNotifiedThings": (integer, False),
         "NumberOfSucceededThings": (integer, False),
```