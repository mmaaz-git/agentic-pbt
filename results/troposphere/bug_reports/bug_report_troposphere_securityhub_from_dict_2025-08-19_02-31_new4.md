# Bug Report: troposphere.securityhub from_dict() Broken for AWSObject Classes

**Target**: `troposphere.securityhub` (all AWSObject classes)
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `from_dict()` method fails for all AWSObject classes in troposphere.securityhub because it cannot handle the output format of `to_dict()`, breaking round-trip serialization.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.securityhub as sh

@given(
    linked_regions=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10),
    region_linking_mode=st.sampled_from(['ALL_REGIONS', 'ALL_REGIONS_EXCEPT', 'SPECIFIED_REGIONS']),
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=256),
        max_size=10
    )
)
def test_aggregator_v2_round_trip(linked_regions, region_linking_mode, tags):
    """Test that AggregatorV2 survives to_dict/from_dict round-trip"""
    obj = sh.AggregatorV2('TestAggregator')
    obj.LinkedRegions = linked_regions
    obj.RegionLinkingMode = region_linking_mode
    if tags:
        obj.Tags = tags
    
    dict_repr = obj.to_dict()
    new_obj = sh.AggregatorV2.from_dict('TestAggregator', dict_repr)
    dict_repr2 = new_obj.to_dict()
    
    assert dict_repr == dict_repr2
```

**Failing input**: `linked_regions=['0'], region_linking_mode='ALL_REGIONS', tags={}`

## Reproducing the Bug

```python
import troposphere.securityhub as sh

obj = sh.AggregatorV2('TestAggregator')
obj.LinkedRegions = ['us-east-1']
obj.RegionLinkingMode = 'ALL_REGIONS'

dict_repr = obj.to_dict()
print(dict_repr)

new_obj = sh.AggregatorV2.from_dict('TestAggregator', dict_repr)
```

## Why This Is A Bug

The `to_dict()` method produces output with a 'Properties' wrapper and 'Type' field:
```
{'Properties': {...}, 'Type': 'AWS::SecurityHub::AggregatorV2'}
```

However, `from_dict()` expects the properties directly, not wrapped. This breaks the fundamental contract that `from_dict(to_dict(obj))` should recreate the object, making serialization/deserialization impossible for all AWSObject classes.

## Fix

The issue is in the base `from_dict` implementation. It needs to unwrap the 'Properties' key when present:

```diff
@classmethod
def from_dict(cls, title, d):
+   # If the dict has the CloudFormation structure, unwrap it
+   if 'Type' in d and 'Properties' in d:
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```