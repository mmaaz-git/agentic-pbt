# Bug Report: troposphere.qbusiness Round-Trip Serialization Failure

**Target**: `troposphere.qbusiness`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `from_dict()` method fails for all AWS Object classes in troposphere.qbusiness, violating the round-trip property that `from_dict(to_dict(obj))` should recreate the object.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.qbusiness as qb

@given(
    display_name=st.text(min_size=1, max_size=100),
    description=st.text(min_size=0, max_size=200),
    include_description=st.booleans()
)
def test_application_round_trip(display_name, description, include_description):
    kwargs = {'DisplayName': display_name}
    if include_description:
        kwargs['Description'] = description
    
    app1 = qb.Application('TestApp', **kwargs)
    app_dict = app1.to_dict()
    app2 = qb.Application.from_dict('TestApp2', app_dict)
    assert app2.to_dict() == app_dict
```

**Failing input**: `display_name='0', description='', include_description=False`

## Reproducing the Bug

```python
import troposphere.qbusiness as qb

app = qb.Application('MyApp', DisplayName='Test Application')
app_dict = app.to_dict()
print(f"Serialized: {app_dict}")

try:
    app_restored = qb.Application.from_dict('MyApp2', app_dict)
    print("Success")
except AttributeError as e:
    print(f"Error: {e}")
```

## Why This Is A Bug

The `to_dict()` method produces a dictionary with structure `{'Properties': {...}, 'Type': '...'}`, but `from_dict()` expects the dictionary to have keys matching the class's `props` attribute directly. This mismatch breaks the fundamental invariant that serialization and deserialization should be inverse operations, preventing users from saving and restoring CloudFormation templates programmatically.

## Fix

The `from_dict` method needs to handle the nested 'Properties' structure that `to_dict` produces. Here's a potential fix:

```diff
@classmethod
def from_dict(cls, title, d):
+   # Handle the nested Properties structure from to_dict()
+   if 'Properties' in d and 'Type' in d:
+       # This is a full CloudFormation resource dict
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```