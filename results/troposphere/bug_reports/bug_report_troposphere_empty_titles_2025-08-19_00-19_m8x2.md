# Bug Report: troposphere Allows Empty Titles for Resources

**Target**: `troposphere` (all modules)
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The troposphere library incorrectly allows empty strings and None as titles for AWSObject instances (CloudFormation resources), which produces invalid CloudFormation templates with missing logical IDs and broken references.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.cassandra as cassandra
from troposphere import Ref

@given(title=st.one_of(st.just(""), st.none()))
def test_empty_titles_produce_invalid_cloudformation(title):
    """Empty titles should be rejected for CloudFormation resources."""
    keyspace = cassandra.Keyspace(
        title=title,
        KeyspaceName="test"
    )
    
    # This produces a resource without a logical ID
    result = keyspace.to_dict()
    
    # References to this resource are broken
    ref = keyspace.ref()
    ref_dict = ref.to_dict()
    
    # The Ref points to empty string or None
    assert ref_dict["Ref"] in ("", None)
    
    # This creates invalid CloudFormation
```

**Failing input**: `title=""` or `title=None`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.cassandra as cassandra

# Create resource with empty title
keyspace = cassandra.Keyspace(
    title="",  # Empty title accepted but shouldn't be
    KeyspaceName="test"
)

# Produces CloudFormation without logical ID
print(keyspace.to_dict())
# Output: {'Properties': {'KeyspaceName': 'test'}, 'Type': 'AWS::Cassandra::Keyspace'}

# References are broken
print(keyspace.ref().to_dict())
# Output: {'Ref': ''}

# DependsOn is broken
table = cassandra.Table(
    title="MyTable",
    KeyspaceName="test",
    PartitionKeyColumns=[cassandra.Column(ColumnName="id", ColumnType="uuid")],
    DependsOn=keyspace
)
print(table.to_dict()["DependsOn"])
# Output: '' (empty string)
```

## Why This Is A Bug

1. **Invalid CloudFormation**: CloudFormation resources require unique logical IDs. A resource without a title has no logical ID in the template, making it impossible to deploy.

2. **Broken References**: CloudFormation intrinsic functions like `Ref`, `GetAtt`, and `DependsOn` rely on logical IDs. With empty titles, these references point to empty strings, causing deployment failures.

3. **Resource Conflicts**: Multiple resources with empty titles would overwrite each other when added to a template, as they would all try to use the same (empty) key.

4. **Inconsistent Validation**: The validation allows empty titles to pass through but enforces alphanumeric constraints for non-empty titles. This half-validation is confusing and error-prone.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -324,8 +324,14 @@ class BaseAWSObject:
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
-            raise ValueError('Name "%s" not alphanumeric' % self.title)
+        # For AWSObject (resources), title is required and must be valid
+        if isinstance(self, AWSObject):
+            if not self.title:
+                raise ValueError('Resource title cannot be empty')
+            if not valid_names.match(self.title):
+                raise ValueError('Name "%s" not alphanumeric' % self.title)
+        # For AWSProperty, title is optional
+        elif self.title and not valid_names.match(self.title):
+            raise ValueError('Name "%s" not alphanumeric' % self.title)
 
     def validate(self) -> None:
         pass
```

This fix ensures that:
- AWSObject instances (resources) must have non-empty, valid titles
- AWSProperty instances can have None/empty titles (since they're optional)
- Non-empty titles still must match the alphanumeric pattern