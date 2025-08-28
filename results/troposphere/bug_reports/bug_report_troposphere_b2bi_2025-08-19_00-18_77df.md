# Bug Report: troposphere.b2bi None Values Not Handled for Optional Properties

**Target**: `troposphere.b2bi` (affects all troposphere modules)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Troposphere raises TypeError when optional properties are set to None, violating Python conventions and breaking common programming patterns.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from hypothesis.strategies import composite
import troposphere.b2bi as b2bi

@composite
def profile_strategy(draw):
    return b2bi.Profile(
        title=draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=255)),
        BusinessName=draw(st.text(min_size=1, max_size=255)),
        Email=draw(st.emails()) if draw(st.booleans()) else None,  # None for optional property
        Logging=draw(st.sampled_from(['ENABLED', 'DISABLED'])),
        Name=draw(st.text(min_size=1, max_size=255)),
        Phone=draw(st.text(min_size=1, max_size=20))
    )

@given(profile_strategy())
def test_profile_round_trip(profile):
    profile_dict = profile.to_dict()
    restored = b2bi.Profile.from_dict(profile.title, profile_dict['Properties'])
    assert profile == restored
```

**Failing input**: `Email=None` when boolean strategy returns False

## Reproducing the Bug

```python
import troposphere.b2bi as b2bi

profile = b2bi.Profile(
    title="TestProfile",
    BusinessName="TestBusiness",
    Email=None,
    Logging="ENABLED",
    Name="TestName",
    Phone="123-456-7890"
)
```

## Why This Is A Bug

Optional properties (marked with `False` in the props definition) should accept None values to indicate absence. The current implementation raises TypeError even though the property is optional, forcing users to:
1. Filter out None values before instantiation
2. Use conditional logic to build kwargs dictionaries
3. Handle explicit null values from external configurations specially

This violates the Python convention where None indicates the absence of a value and makes the API less intuitive.

## Fix

The issue is in `troposphere/__init__.py` in the `BaseAWSObject.__setattr__` method. It needs to handle None values for optional properties:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -248,6 +248,11 @@ class BaseAWSObject:
             return None
         elif name in self.propnames:
             # Check the type of the object and compare against what we were
             # expecting.
             expected_type = self.props[name][0]
+            required = self.props[name][1]
+            
+            # Allow None for optional properties
+            if value is None and not required:
+                return self.properties.__setitem__(name, value)
 
             # If the value is a AWSHelperFn we can't do much validation
             # we'll have to leave that to Amazon. Maybe there's another way
```