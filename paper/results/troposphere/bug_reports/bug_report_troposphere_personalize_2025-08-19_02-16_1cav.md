# Bug Report: troposphere.personalize HpoResourceConfig Accepts Invalid Values

**Target**: `troposphere.personalize.HpoResourceConfig`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

HpoResourceConfig accepts non-numeric strings and invalid numeric values (zero/negative) for MaxNumberOfTrainingJobs and MaxParallelTrainingJobs fields, which should represent positive integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(
    max_jobs=st.text(min_size=1, max_size=20),
    max_parallel=st.text(min_size=1, max_size=20)
)
def test_hpo_resource_config_numeric_validation(max_jobs, max_parallel):
    obj = personalize.HpoResourceConfig(
        MaxNumberOfTrainingJobs=max_jobs,
        MaxParallelTrainingJobs=max_parallel
    )
    result = obj.to_dict()
    
    for field_name, field_value in [
        ('MaxNumberOfTrainingJobs', result.get('MaxNumberOfTrainingJobs')),
        ('MaxParallelTrainingJobs', result.get('MaxParallelTrainingJobs'))
    ]:
        if field_value is not None:
            num_value = int(field_value)
            assert num_value > 0
```

**Failing input**: `max_jobs=':', max_parallel='0'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import personalize

config1 = personalize.HpoResourceConfig(
    MaxNumberOfTrainingJobs='not_a_number',
    MaxParallelTrainingJobs='also_not_a_number'
)
print("Non-numeric strings:", config1.to_dict())

config2 = personalize.HpoResourceConfig(
    MaxNumberOfTrainingJobs='0',
    MaxParallelTrainingJobs='-5'
)
print("Invalid numeric values:", config2.to_dict())
```

## Why This Is A Bug

These fields represent counts of training jobs and must be positive integers. AWS Personalize expects valid positive integer strings. The library should validate these constraints to prevent invalid CloudFormation templates.

## Fix

```diff
--- a/troposphere/personalize.py
+++ b/troposphere/personalize.py
@@ -152,10 +152,23 @@ class HpoResourceConfig(AWSProperty):
     `HpoResourceConfig <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-personalize-solution-hporesourceconfig.html>`__
     """
 
     props: PropsDictType = {
         "MaxNumberOfTrainingJobs": (str, False),
         "MaxParallelTrainingJobs": (str, False),
     }
 
+    def validate(self):
+        super().validate()
+        for field_name in ['MaxNumberOfTrainingJobs', 'MaxParallelTrainingJobs']:
+            if field_name in self.properties:
+                value = self.properties[field_name]
+                try:
+                    num_value = int(value)
+                    if num_value <= 0:
+                        raise ValueError(f"{field_name} must be a positive integer, got {num_value}")
+                except (ValueError, TypeError):
+                    raise ValueError(f"{field_name} must be a numeric string, got '{value}'")
+        return True
```