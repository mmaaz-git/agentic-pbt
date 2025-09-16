# Bug Report: troposphere.sagemaker API Inconsistency Between to_dict() and from_dict()

**Target**: `troposphere.sagemaker` (all AWS resource classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `to_dict()` and `from_dict()` methods have inconsistent APIs: `to_dict()` returns a full CloudFormation resource format with 'Type' and 'Properties' keys, but `from_dict()` expects only the Properties portion, not the full format.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import troposphere.sagemaker as sm

ASCII_ALPHANUMERIC = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

@given(
    title=st.text(alphabet=ASCII_ALPHANUMERIC, min_size=1, max_size=63),
    domain_name=st.text(alphabet=ASCII_ALPHANUMERIC + '-', min_size=1, max_size=63),
    vpc_id=st.text(alphabet=ASCII_ALPHANUMERIC, min_size=4, max_size=20).map(lambda x: f"vpc-{x}"),
    subnet_ids=st.lists(
        st.text(alphabet=ASCII_ALPHANUMERIC, min_size=4, max_size=20).map(lambda x: f"subnet-{x}"),
        min_size=1, max_size=5
    ),
    auth_mode=st.sampled_from(['IAM', 'SSO'])
)
@settings(max_examples=100)
def test_to_dict_from_dict_inconsistency(title, domain_name, vpc_id, subnet_ids, auth_mode):
    domain = sm.Domain(title)
    domain.DomainName = domain_name
    domain.VpcId = vpc_id
    domain.SubnetIds = subnet_ids
    domain.AuthMode = auth_mode
    domain.DefaultUserSettings = sm.UserSettings()
    
    # to_dict returns full CloudFormation resource format
    dict_repr = domain.to_dict()
    
    # This fails with "Object type Domain does not have a Properties property"
    # new_domain = sm.Domain.from_dict('New', dict_repr)
    
    # This works - must extract Properties manually
    new_domain = sm.Domain.from_dict(title + '2', dict_repr['Properties'])
    
    # Verify round-trip preserves properties
    new_dict = new_domain.to_dict()
    assert dict_repr['Properties'] == new_dict['Properties']
```

**Failing input**: When attempting `sm.Domain.from_dict('New', dict_repr)` where `dict_repr` is the output of `to_dict()`

## Reproducing the Bug

```python
import troposphere.sagemaker as sm

# Create a Domain instance
domain = sm.Domain('TestDomain')
domain.DomainName = 'test-domain'
domain.VpcId = 'vpc-12345'
domain.SubnetIds = ['subnet-1', 'subnet-2']
domain.AuthMode = 'IAM'
domain.DefaultUserSettings = sm.UserSettings()

# Serialize to dict
dict_repr = domain.to_dict()
print(f"to_dict() returns: {list(dict_repr.keys())}")
# Output: ['Properties', 'Type']

# Attempting to deserialize the full dict fails
try:
    new_domain = sm.Domain.from_dict('TestDomain2', dict_repr)
except AttributeError as e:
    print(f"Error: {e}")
    # Output: Object type Domain does not have a Properties property

# Must manually extract Properties for from_dict to work
new_domain = sm.Domain.from_dict('TestDomain2', dict_repr['Properties'])
print("Success when using dict_repr['Properties']")
```

## Why This Is A Bug

This violates the principle of least surprise and creates an inconsistent API. Users naturally expect that `from_dict(to_dict(obj))` should work as a round-trip operation. The current behavior requires users to know that:
1. `to_dict()` produces CloudFormation format with 'Type' and 'Properties'
2. `from_dict()` expects only the Properties portion

This inconsistency affects all AWS resource classes in troposphere (not just sagemaker), making it a systematic API design issue that can confuse users and lead to errors.

## Fix

The issue could be fixed by either:

1. **Option A**: Make `from_dict()` accept the full CloudFormation format:

```diff
# In troposphere/__init__.py, in the from_dict method
@classmethod
def from_dict(cls, title, d):
+   # Handle both full CloudFormation format and Properties-only format
+   if 'Type' in d and 'Properties' in d:
+       # Extract Properties from full format
+       d = d['Properties']
    return cls._from_dict(title, **d)
```

2. **Option B**: Add a new method `from_cloudformation_dict()` that handles the full format, keeping backward compatibility:

```diff
# In troposphere/__init__.py, add new method to BaseAWSObject
@classmethod
+def from_cloudformation_dict(cls, title, cf_dict):
+    """Create an instance from a CloudFormation resource dict (with Type and Properties)."""
+    if 'Properties' not in cf_dict:
+        raise ValueError("CloudFormation dict must have 'Properties' key")
+    return cls.from_dict(title, cf_dict['Properties'])
```

Option A would be more user-friendly as it makes the round-trip work transparently.