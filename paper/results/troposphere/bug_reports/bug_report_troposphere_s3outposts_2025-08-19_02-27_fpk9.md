# Bug Report: troposphere.s3outposts Round-Trip Serialization Failure

**Target**: `troposphere.s3outposts` (all resource classes)
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `from_dict()` method fails to deserialize the output of `to_dict()` for all AWS resource classes in the troposphere.s3outposts module, breaking round-trip serialization.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.s3outposts as s3o

@given(
    bucket_name=st.text(min_size=1, max_size=63),
    outpost_id=st.text(min_size=1, max_size=100)
)
def test_bucket_round_trip_from_dict_to_dict(bucket_name, outpost_id):
    """Test that Bucket.from_dict(obj.to_dict()) creates an equivalent object"""
    assume(bucket_name.strip() != "")
    assume(outpost_id.strip() != "")
    
    bucket1 = s3o.Bucket('TestBucket', 
                        BucketName=bucket_name,
                        OutpostId=outpost_id)
    
    dict_repr = bucket1.to_dict()
    bucket2 = s3o.Bucket.from_dict('TestBucket2', dict_repr)
    dict_repr2 = bucket2.to_dict()
    
    assert dict_repr == dict_repr2
```

**Failing input**: `bucket_name='0', outpost_id='0'`

## Reproducing the Bug

```python
import troposphere.s3outposts as s3o

bucket = s3o.Bucket('MyBucket', 
    BucketName='test-bucket',
    OutpostId='op-12345')

dict_repr = bucket.to_dict()
print('to_dict() output:', dict_repr)

bucket2 = s3o.Bucket.from_dict('MyBucket2', dict_repr)
```

## Why This Is A Bug

The `to_dict()` method produces a dictionary with a structure like:
```python
{'Properties': {'BucketName': 'test-bucket', 'OutpostId': 'op-12345'}, 'Type': 'AWS::S3Outposts::Bucket'}
```

However, `from_dict()` expects the properties directly without the 'Properties' wrapper. This violates the round-trip property that `from_dict(to_dict(x))` should recreate the original object. The same issue affects all resource classes: Bucket, AccessPoint, BucketPolicy, and Endpoint.

## Fix

The `from_dict()` method should handle the full CloudFormation template format that `to_dict()` produces:

```diff
@classmethod
def from_dict(cls, title, d):
+   # Handle CloudFormation template format
+   if 'Properties' in d and 'Type' in d:
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```

Alternatively, properly parse the nested structure:

```diff
@classmethod
def _from_dict(cls, title=None, **kwargs):
    props = {}
    for prop_name, value in kwargs.items():
+       # Skip Type field
+       if prop_name == 'Type':
+           continue
+       # Handle Properties wrapper
+       if prop_name == 'Properties':
+           return cls._from_dict(title, **value)
        try:
            prop_attrs = cls.props[prop_name]
```