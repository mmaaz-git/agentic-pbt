# Bug Report: troposphere.kms Empty Title Validation Bypass

**Target**: `troposphere.kms` (affects all troposphere AWS resources)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Empty string titles bypass validation in troposphere AWS resource classes, allowing creation of resources without logical IDs, which violates CloudFormation requirements.

## Property-Based Test

```python
@given(st.text())
def test_kms_key_title_validation(title):
    """KMS Key titles must be alphanumeric only"""
    is_valid = title and all(c.isalnum() for c in title)
    
    if is_valid:
        key = kms.Key(title)
        assert key.title == title
    else:
        with pytest.raises(ValueError, match='Name .* not alphanumeric'):
            kms.Key(title)
```

**Failing input**: `''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.kms as kms

key = kms.Key('')
print(f"Created Key with empty title: {repr(key.title)}")

key_dict = key.to_dict()
print(f"Converted to dict: {key_dict}")

alias = kms.Alias('', AliasName="alias/test", TargetKeyId="key-123")
print(f"Created Alias with empty title: {repr(alias.title)}")

replica = kms.ReplicaKey('', 
                        KeyPolicy={'Version': '2012-10-17'},
                        PrimaryKeyArn='arn:aws:kms:us-east-1:123456789012:key/12345678')
print(f"Created ReplicaKey with empty title: {repr(replica.title)}")
```

## Why This Is A Bug

CloudFormation requires all resources to have non-empty logical IDs. The title in troposphere becomes the logical ID in CloudFormation templates. Empty titles should be rejected during validation, but the validation is skipped when title is an empty string due to a conditional check that only validates when `self.title` is truthy.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,8 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        if self.title is not None:
+            self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```