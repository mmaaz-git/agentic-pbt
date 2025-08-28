# Bug Report: troposphere.personalize Invalid Hyperparameter Ranges Accepted

**Target**: `troposphere.personalize`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The troposphere.personalize module fails to validate hyperparameter ranges, allowing MaxValue < MinValue in both IntegerHyperParameterRange and ContinuousHyperParameterRange classes, generating invalid CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st

@given(
    name=st.text(min_size=1, max_size=50),
    min_val=st.integers(min_value=-1000000, max_value=1000000),
    max_val=st.integers(min_value=-1000000, max_value=1000000)
)
def test_integer_hyperparameter_range_invariant(name, min_val, max_val):
    obj = personalize.IntegerHyperParameterRange(
        Name=name,
        MinValue=min_val,
        MaxValue=max_val
    )
    result = obj.to_dict()
    if 'MinValue' in result and 'MaxValue' in result:
        assert result['MaxValue'] >= result['MinValue']
```

**Failing input**: `name='0', min_val=0, max_val=-1`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import personalize, Template
import json

invalid_range = personalize.IntegerHyperParameterRange(
    Name='epochs',
    MinValue=100,
    MaxValue=10
)

template = Template()
solution = personalize.Solution(
    'MySolution',
    DatasetGroupArn='arn:aws:personalize:us-east-1:123456789012:dataset-group/test',
    Name='MySolution',
    SolutionConfig=personalize.SolutionConfig(
        HpoConfig=personalize.HpoConfig(
            AlgorithmHyperParameterRanges=personalize.AlgorithmHyperParameterRanges(
                IntegerHyperParameterRanges=[invalid_range]
            )
        )
    )
)
template.add_resource(solution)

output = json.loads(template.to_json())
range_cfg = output['Resources']['MySolution']['Properties']['SolutionConfig']['HpoConfig']['AlgorithmHyperParameterRanges']['IntegerHyperParameterRanges'][0]
print(f"MinValue: {range_cfg['MinValue']}, MaxValue: {range_cfg['MaxValue']}")
```

## Why This Is A Bug

Hyperparameter ranges with MaxValue < MinValue are semantically invalid and would be rejected by AWS Personalize. The library should validate this constraint to prevent generating invalid CloudFormation templates.

## Fix

```diff
--- a/troposphere/personalize.py
+++ b/troposphere/personalize.py
@@ -116,10 +116,18 @@ class IntegerHyperParameterRange(AWSProperty):
     `IntegerHyperParameterRange <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-personalize-solution-integerhyperparameterrange.html>`__
     """
 
     props: PropsDictType = {
         "MaxValue": (integer, False),
         "MinValue": (integer, False),
         "Name": (str, False),
     }
 
+    def validate(self):
+        super().validate()
+        if 'MinValue' in self.properties and 'MaxValue' in self.properties:
+            min_val = self.properties['MinValue']
+            max_val = self.properties['MaxValue']
+            if max_val < min_val:
+                raise ValueError(f"MaxValue ({max_val}) must be >= MinValue ({min_val})")
+        return True

@@ -104,10 +104,18 @@ class ContinuousHyperParameterRange(AWSProperty):
     `ContinuousHyperParameterRange <http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-personalize-solution-continuoushyperparameterrange.html>`__
     """
 
     props: PropsDictType = {
         "MaxValue": (double, False),
         "MinValue": (double, False),
         "Name": (str, False),
     }
 
+    def validate(self):
+        super().validate()
+        if 'MinValue' in self.properties and 'MaxValue' in self.properties:
+            min_val = self.properties['MinValue']
+            max_val = self.properties['MaxValue']
+            if max_val < min_val:
+                raise ValueError(f"MaxValue ({max_val}) must be >= MinValue ({min_val})")
+        return True
```