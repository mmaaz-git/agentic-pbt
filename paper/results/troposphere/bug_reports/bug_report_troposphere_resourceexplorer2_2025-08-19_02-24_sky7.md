# Bug Report: troposphere AWSObject Round-Trip Serialization Failure

**Target**: `troposphere.resourceexplorer2` (affects all AWSObject classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict()` method cannot deserialize the output of `to_dict()` for AWSObject classes, breaking the round-trip serialization contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.resourceexplorer2 as re2

@given(view_name=st.text(min_size=0, max_size=1000))
def test_view_roundtrip(view_name):
    """View to_dict/from_dict round-trip should work"""
    original = re2.View('TestView', ViewName=view_name)
    dict_repr = original.to_dict()
    
    # This should work but raises AttributeError
    recreated = re2.View.from_dict('TestView', dict_repr)
    recreated_dict = recreated.to_dict()
    assert dict_repr == recreated_dict
```

**Failing input**: Any input (e.g., `view_name=''`)

## Reproducing the Bug

```python
import troposphere.resourceexplorer2 as re2

# Create any AWSObject instance
view = re2.View('MyView', ViewName='test-view')

# Serialize to dict
view_dict = view.to_dict()
print(view_dict)
# {'Properties': {'ViewName': 'test-view'}, 'Type': 'AWS::ResourceExplorer2::View'}

# Try to deserialize - this fails
recreated_view = re2.View.from_dict('MyView', view_dict)
# AttributeError: Object type View does not have a Properties property.
```

## Why This Is A Bug

The `to_dict()` and `from_dict()` methods form a serialization/deserialization pair. Users reasonably expect that `from_dict(name, obj.to_dict())` should recreate the object. The current implementation violates this fundamental round-trip property because:

1. `to_dict()` returns: `{'Properties': {...}, 'Type': '...'}`
2. `from_dict()` expects: `{...}` (just the properties, no wrapper)

This affects all AWSObject subclasses across the entire troposphere library, not just resourceexplorer2.

## Fix

The `from_dict` method should handle the `Properties` wrapper that `to_dict` produces. Here's a potential fix to the `_from_dict` method in troposphere's BaseAWSObject class:

```diff
@classmethod
def _from_dict(cls, title=None, **kwargs):
+   # Handle the case where to_dict output is passed
+   if 'Properties' in kwargs and 'Type' in kwargs:
+       # Extract just the properties from the to_dict format
+       kwargs = kwargs['Properties']
+   
    props = {}
    for prop_name, value in kwargs.items():
        try:
            prop_attrs = cls.props[prop_name]
        except KeyError:
            raise AttributeError(
                "Object type %s does not have a "
                "%s property." % (cls.__name__, prop_name)
            )
        # ... rest of the method
```

Alternatively, update documentation to clarify that `from_dict` expects unwrapped properties and is not compatible with `to_dict` output.