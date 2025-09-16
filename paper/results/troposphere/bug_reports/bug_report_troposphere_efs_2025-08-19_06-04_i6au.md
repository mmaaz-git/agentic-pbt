# Bug Report: troposphere.efs Round-Trip Property Violation

**Target**: `troposphere.efs` (all AWSObject classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `to_dict()` and `from_dict()` methods in troposphere.efs AWSObject classes violate the round-trip property - objects cannot be reconstructed from their dictionary representation.

## Property-Based Test

```python
@given(
    st.booleans(),  # Encrypted
    st.booleans(),  # BypassPolicyLockoutSafetyCheck
    st.sampled_from([None, "generalPurpose", "maxIO"]),  # PerformanceMode
    st.sampled_from([None, Bursting, Elastic, Provisioned])  # ThroughputMode
)
def test_filesystem_roundtrip(encrypted, bypass, perf_mode, throughput_mode):
    """Property: FileSystem to_dict and from_dict should preserve data"""
    fs = efs.FileSystem(title="TestFS")
    
    if encrypted:
        fs.Encrypted = encrypted
    if bypass:
        fs.BypassPolicyLockoutSafetyCheck = bypass
    if perf_mode:
        fs.PerformanceMode = perf_mode
    if throughput_mode:
        fs.ThroughputMode = throughput_mode
    
    # Convert to dict and back
    dict_repr = fs.to_dict()
    fs_recovered = efs.FileSystem.from_dict("TestFS", dict_repr)
    dict_recovered = fs_recovered.to_dict()
    
    # The round-trip should preserve the data
    assert dict_repr == dict_recovered
```

**Failing input**: Any input - the test fails immediately with even an empty FileSystem object

## Reproducing the Bug

```python
import troposphere.efs as efs

fs = efs.FileSystem(title="TestFS")
dict_repr = fs.to_dict()
print(dict_repr)
# Output: {'Type': 'AWS::EFS::FileSystem'}

fs_recovered = efs.FileSystem.from_dict("TestFS", dict_repr)
# AttributeError: Object type FileSystem does not have a Type property.
```

## Why This Is A Bug

The `to_dict()` method adds CloudFormation template keys like 'Type' and 'Properties' to the dictionary representation, but `from_dict()` expects only the actual property names defined in the class's `props` attribute. This breaks the fundamental expectation that `from_dict(to_dict(obj))` should reconstruct the original object.

This affects all AWSObject classes in the module (FileSystem, AccessPoint, MountTarget).

## Fix

The `from_dict()` method should filter out CloudFormation template keys before processing properties:

```diff
@classmethod
def _from_dict(
    cls: Type[__BaseAWSObjectTypeVar], title: Optional[str] = None, **kwargs: Any
) -> __BaseAWSObjectTypeVar:
    props: Dict[str, Any] = {}
+   # Filter out CloudFormation template keys
+   template_keys = {'Type', 'Properties', 'DependsOn', 'Metadata', 'UpdatePolicy', 'Condition', 'DeletionPolicy'}
+   if 'Properties' in kwargs:
+       kwargs = kwargs['Properties']
+   kwargs = {k: v for k, v in kwargs.items() if k not in template_keys}
    for prop_name, value in kwargs.items():
        try:
            prop_attrs = cls.props[prop_name]
```