# Bug Report: troposphere.proton API Inconsistency in to_dict() Method

**Target**: `troposphere.proton` (EnvironmentTemplate, ServiceTemplate, EnvironmentAccountConnection)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `to_dict()` method inconsistently includes or excludes the 'Properties' key based on whether properties are set, breaking API predictability and the round-trip property.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.proton as proton

@given(st.text(alphabet=st.characters(whitelist_categories=['Lu', 'Ll', 'Nd']), min_size=1))
def test_to_dict_always_has_properties_key(title):
    """Test that to_dict() always includes Properties key for consistency"""
    template = proton.EnvironmentTemplate(title)
    dict_output = template.to_dict()
    # This fails - Properties key is missing when no properties are set
    assert 'Properties' in dict_output
```

**Failing input**: Any valid title when template has no properties set

## Reproducing the Bug

```python
import troposphere.proton as proton

# Template with no properties
empty_template = proton.EnvironmentTemplate('EmptyTemplate')
empty_dict = empty_template.to_dict()

# Template with properties
template_with_props = proton.EnvironmentTemplate('WithProps', Name='Test')
props_dict = template_with_props.to_dict()

# Inconsistent behavior
print(f"Empty template dict: {empty_dict}")
print(f"With props dict: {props_dict}")

# This will raise KeyError
try:
    properties = empty_dict['Properties']
except KeyError:
    print("KeyError: 'Properties' key missing when no properties set")

# This works fine
properties = props_dict['Properties']
print(f"Properties found: {properties}")
```

## Why This Is A Bug

This violates the API consistency principle. Users cannot reliably access `dict['Properties']` without defensive programming. The to_dict() method should always return a consistent structure regardless of whether properties are set, just with an empty dict for Properties when no properties exist. This inconsistency breaks code that expects a uniform dictionary structure and violates the round-trip property `from_dict(to_dict(x)['Properties'])`.

## Fix

The fix would ensure `to_dict()` always includes the 'Properties' key, even when empty:

```diff
# In the to_dict() method implementation
def to_dict(self):
    d = {}
    if self.resource_type:
        d['Type'] = self.resource_type
    
    properties = self._get_properties_dict()  # Gets actual properties
-   if properties:
-       d['Properties'] = properties
+   # Always include Properties key for consistency
+   d['Properties'] = properties if properties else {}
    
    return d
```