# Bug Report: troposphere.validators.tags_or_list Rejects Dictionary Input

**Target**: `troposphere.validators.tags_or_list`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `tags_or_list()` validator function rejects dictionary inputs, even though CloudFormation commonly uses dictionaries to represent tags, causing valid tag configurations to fail validation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import appstream

@given(tags=st.dictionaries(
    st.text(min_size=1, max_size=128),
    st.text(min_size=0, max_size=256),
    max_size=50
))
def test_tags_validator_should_accept_dicts(tags):
    """Tags validator should accept dictionaries"""
    # This raises ValueError but shouldn't
    ab = appstream.AppBlock(
        'TestBlock',
        Name='Test',
        SourceS3Location=appstream.S3Location(S3Bucket='b', S3Key='k'),
        Tags=tags
    )
```

**Failing input**: `{}`, `{'key': 'value'}`, any dictionary

## Reproducing the Bug

```python
from troposphere import appstream

# This should work but raises ValueError
ab = appstream.AppBlock(
    'TestAppBlock',
    Name='TestBlock',
    SourceS3Location=appstream.S3Location(S3Bucket='bucket', S3Key='key'),
    Tags={'Environment': 'Production', 'Owner': 'TeamA'}
)
# ValueError: Value {'Environment': 'Production', 'Owner': 'TeamA'} 
# of type <class 'dict'> must be either Tags or list
```

## Why This Is A Bug

CloudFormation templates commonly represent tags as dictionaries in both JSON and YAML formats. The validator should accept dictionaries as a valid representation of tags, converting them internally to the Tags type if needed. This restriction forces users to use the Tags class explicitly, reducing usability.

## Fix

```diff
def tags_or_list(x: Any) -> Union[AWSHelperFn, Tags, List[Any]]:
     """backward compatibility"""
     from .. import AWSHelperFn, Tags
 
     if isinstance(x, (AWSHelperFn, Tags, list)):
         return x  # type: ignore
+    
+    # Accept dictionaries and convert to Tags
+    if isinstance(x, dict):
+        return Tags(x)
 
     raise ValueError(f"Value {x} of type {type(x)} must be either Tags or list")
```