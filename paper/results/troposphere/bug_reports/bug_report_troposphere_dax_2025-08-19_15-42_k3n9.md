# Bug Report: troposphere.dax Title Validation Bypass

**Target**: `troposphere.dax.Cluster` (and all `BaseAWSObject` subclasses)
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The title validation in troposphere's BaseAWSObject accepts empty strings and None values, which violates CloudFormation's requirement for alphanumeric resource identifiers and causes JSON serialization errors.

## Property-Based Test

```python
@given(st.text())
def test_title_validation(title):
    """Test that only alphanumeric titles are accepted"""
    is_valid = bool(title and title.isalnum())
    
    if is_valid:
        # Should create successfully
        obj = dax.Cluster(
            title,
            IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
            NodeType="dax.r3.large",
            ReplicationFactor=1
        )
        assert obj.title == title
    else:
        # Should raise ValueError for invalid titles
        with pytest.raises(ValueError) as exc_info:
            dax.Cluster(
                title,
                IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
                NodeType="dax.r3.large",
                ReplicationFactor=1
            )
        assert 'not alphanumeric' in str(exc_info.value)
```

**Failing input**: `title=''` and `title=None`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Template
import troposphere.dax as dax

# Bug 1: Empty string accepted as title
cluster1 = dax.Cluster(
    "",  # Empty title - should be rejected!
    IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
    NodeType="dax.r3.large",
    ReplicationFactor=1
)
print(f"Empty title accepted: '{cluster1.title}'")

# Bug 2: None accepted as title  
cluster2 = dax.Cluster(
    None,  # None title - should be rejected!
    IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole2",
    NodeType="dax.r3.large",
    ReplicationFactor=1
)
print(f"None title accepted: {cluster2.title}")

# Adding to template causes TypeError
template = Template()
template.add_resource(cluster1)
template.add_resource(cluster2)

# This fails with: TypeError: '<' not supported between instances of 'NoneType' and 'str'
template.to_json()
```

## Why This Is A Bug

1. **CloudFormation Contract Violation**: CloudFormation requires resource logical IDs to be alphanumeric. Empty strings and None are invalid identifiers that violate this contract.

2. **Silent Failure Path**: The `validate_title()` method in BaseAWSObject skips validation when `self.title` is falsy, allowing invalid titles to pass through:
   ```python
   def validate_title(self) -> None:
       if not self.title or not valid_names.match(self.title):
           raise ValueError('Name "%s" not alphanumeric' % self.title)
   ```

3. **Runtime Errors**: None titles cause TypeErrors during JSON serialization when `sort_keys=True` tries to compare None with strings.

4. **Template Corruption**: Empty string titles create CloudFormation templates with empty resource keys, which are invalid.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -324,7 +324,10 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if self.title is None:
+            raise ValueError('Title cannot be None')
+        if not self.title:
+            raise ValueError('Title cannot be empty')
+        if not valid_names.match(self.title):
             raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
```

This fix ensures that:
1. None titles are explicitly rejected with a clear error message
2. Empty string titles are explicitly rejected with a clear error message  
3. Non-alphanumeric titles continue to be rejected as before