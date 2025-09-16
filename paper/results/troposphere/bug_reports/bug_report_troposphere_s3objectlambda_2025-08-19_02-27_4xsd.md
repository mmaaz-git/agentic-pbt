# Bug Report: troposphere.s3objectlambda AWSObject Constructor Misleading Signature

**Target**: `troposphere.s3objectlambda.AccessPoint`, `troposphere.s3objectlambda.AccessPointPolicy` 
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

AWSObject subclasses in troposphere.s3objectlambda have a misleading constructor signature where `title` is typed as `Optional[str]` but cannot be omitted when calling the constructor, causing TypeError when properties are passed without the title argument.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.s3objectlambda import AccessPointPolicy

@given(
    access_point=st.text(min_size=1),
    policy_doc=st.dictionaries(st.text(min_size=1), st.text())
)
def test_access_point_policy_initialization(access_point, policy_doc):
    # This should work based on the Optional[str] type hint for title
    policy = AccessPointPolicy(
        ObjectLambdaAccessPoint=access_point,
        PolicyDocument=policy_doc
    )
    assert policy.to_dict()['Properties']['ObjectLambdaAccessPoint'] == access_point
```

**Failing input**: `access_point='0', policy_doc={}`

## Reproducing the Bug

```python
from troposphere.s3objectlambda import AccessPointPolicy

policy = AccessPointPolicy(
    ObjectLambdaAccessPoint="test-ap",
    PolicyDocument={"Version": "2012-10-17"}
)
```

## Why This Is A Bug

The constructor signature indicates `title: Optional[str]` which suggests the title parameter can be None or omitted. However, attempting to create an instance without providing the title argument (either positionally or as keyword) results in `TypeError: BaseAWSObject.__init__() missing 1 required positional argument: 'title'`. 

This violates the API contract implied by the type hints. Users must either:
1. Pass title positionally: `AccessPointPolicy("MyPolicy", ...)`  
2. Pass title as keyword: `AccessPointPolicy(title="MyPolicy", ...)`
3. Pass None explicitly: `AccessPointPolicy(None, ...)`

But cannot omit it entirely, despite the Optional type hint suggesting this should be valid.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -159,7 +159,7 @@ class BaseAWSObject:
 
     def __init__(
         self,
-        title: Optional[str],
+        title: Optional[str] = None,
         template: Optional[Template] = None,
         validation: bool = True,
         **kwargs: Any,
```

This change would make the title parameter truly optional with a default value of None, matching the behavior implied by the Optional[str] type hint.