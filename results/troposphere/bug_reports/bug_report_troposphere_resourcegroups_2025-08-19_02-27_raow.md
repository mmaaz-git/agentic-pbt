# Bug Report: troposphere.resourcegroups Misleading Error Message for Invalid List Elements

**Target**: `troposphere.resourcegroups`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

When a None value is included in a list field that expects strings (e.g., TagFilter.Values), the error message incorrectly suggests the entire field is None rather than indicating a specific list element is invalid.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.resourcegroups as rg

@given(
    key=st.one_of(st.none(), st.just(""), st.text(min_size=1)),
    values=st.one_of(
        st.none(),
        st.just([]),
        st.lists(st.one_of(st.none(), st.just(""), st.text()), max_size=5)
    )
)
def test_tag_filter_none_empty(key, values):
    """Test TagFilter with None and empty values"""
    kwargs = {}
    if key is not None:
        kwargs['Key'] = key
    if values is not None:
        kwargs['Values'] = values
    
    tf = rg.TagFilter(**kwargs)
    dict_repr = tf.to_dict()
    
    if key is not None:
        assert dict_repr.get('Key') == key
    else:
        assert 'Key' not in dict_repr
        
    if values is not None:
        assert dict_repr.get('Values') == values
    else:
        assert 'Values' not in dict_repr
```

**Failing input**: `key=None, values=[None]`

## Reproducing the Bug

```python
import troposphere.resourcegroups as rg

tf = rg.TagFilter(Key='test', Values=['valid', None, 'another'])
```

## Why This Is A Bug

The error message "TypeError: <class 'troposphere.resourcegroups.TagFilter'>: None.Values is <class 'NoneType'>, expected [<class 'str'>]" is misleading. It suggests that the entire Values field is None, when actually an element within the Values list is None. The error should clearly indicate that a list element has an invalid type.

This affects all AWS property classes that have list fields with type constraints, including ConfigurationParameter, TagFilter, and others.

## Fix

The issue is in the `_raise_type` method in troposphere/__init__.py. When validating list elements, it should provide a more informative error message:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -289,9 +289,10 @@ class BaseAWSObject:
                 # type checks (as above accept AWSHelperFn because
                 # we can't do the validation ourselves)
-                for v in cast(List[Any], value):
+                for i, v in enumerate(cast(List[Any], value)):
                     if not isinstance(v, tuple(expected_type)) and not isinstance(
                         v, AWSHelperFn
                     ):
-                        self._raise_type(name, v, expected_type)
+                        raise TypeError(
+                            "%s: Element at index %d in %s is %s, expected one of %s"
+                            % (self.__class__, i, name, type(v), expected_type)
+                        )
                 # Validated so assign it
```