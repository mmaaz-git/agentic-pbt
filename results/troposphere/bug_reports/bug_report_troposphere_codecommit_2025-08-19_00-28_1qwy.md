# Bug Report: troposphere.codecommit None Handling for Optional Properties

**Target**: `troposphere.codecommit`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The troposphere library raises TypeError when None is passed for optional properties in codecommit module classes, violating the expected behavior that optional properties should accept None values.

## Property-Based Test

```python
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.text(min_size=0, max_size=1000),
    st.text(min_size=0, max_size=100),
)
def test_repository_optional_properties(repo_name, description, kms_key):
    """Test Repository with optional properties set to None"""
    repo = codecommit.Repository(
        "MyRepo",
        RepositoryName=repo_name,
        RepositoryDescription=description if description else None,
        KmsKeyId=kms_key if kms_key else None
    )
    dict_repr = repo.to_dict()
    assert dict_repr["Properties"]["RepositoryName"] == repo_name
```

**Failing input**: `repo_name='0', description='', kms_key=''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codecommit as codecommit

# Bug 1: Repository with None for optional property
repo = codecommit.Repository(
    "MyRepo",
    RepositoryName="TestRepo",
    RepositoryDescription=None
)

# Bug 2: Trigger with None for optional properties
trigger = codecommit.Trigger(
    Name="TestTrigger",
    DestinationArn="arn:aws:sns:us-east-1:123456789012:MyTopic",
    Events=["createReference"],
    Branches=None,
    CustomData=None
)

# Bug 3: S3 with None for optional property
s3 = codecommit.S3(
    Bucket="my-bucket",
    Key="my-key",
    ObjectVersion=None
)

# Bug 4: Code with None for optional property
s3_obj = codecommit.S3(Bucket="bucket", Key="key")
code = codecommit.Code(
    S3=s3_obj,
    BranchName=None
)
```

## Why This Is A Bug

Optional properties in the props dictionary have `False` as their second tuple element, indicating they are not required. Users reasonably expect to pass None for optional properties, especially when building objects programmatically where None is a common sentinel value for "not provided". The current behavior forces users to conditionally build kwargs dictionaries, making the API harder to use.

## Fix

The fix requires modifying the BaseAWSObject.__setattr__ method in troposphere/__init__.py to handle None values for optional properties. When a property value is None and the property is optional (required=False), the property should simply not be set rather than raising a TypeError.

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,10 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
+            # Handle None for optional properties
+            required = self.props[name][1]
+            if value is None and not required:
+                return None  # Don't set the property
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
```