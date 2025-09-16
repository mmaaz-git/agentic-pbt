# Bug Report: troposphere.forecast Mutation of Shared List References

**Target**: `troposphere.forecast`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The Schema class in troposphere.forecast stores a reference to the provided Attributes list instead of creating a copy, allowing external mutations to affect the Schema object after creation.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import troposphere.forecast as forecast

@st.composite
def attribute_lists(draw):
    """Generate lists of AttributesItems"""
    num_attrs = draw(st.integers(min_value=1, max_value=5))
    return [
        forecast.AttributesItems(
            AttributeName=f"attr_{i}",
            AttributeType=draw(st.sampled_from(["string", "integer", "float", "timestamp"]))
        )
        for i in range(num_attrs)
    ]

@given(attribute_lists())
@settings(max_examples=50)
def test_schema_mutation_property(attrs):
    """Property: Schema should not be affected by mutations to the original list"""
    original_length = len(attrs)
    
    schema = forecast.Schema(Attributes=attrs)
    dict_before = schema.to_dict()
    attrs_before = dict_before["Attributes"]
    
    attrs.append(
        forecast.AttributesItems(AttributeName="mutated", AttributeType="string")
    )
    
    dict_after = schema.to_dict()
    attrs_after = dict_after["Attributes"]
    
    assert len(attrs_after) == original_length, f"Schema was mutated! Before: {len(attrs_before)}, After: {len(attrs_after)}"
```

**Failing input**: `attrs=[<troposphere.forecast.AttributesItems object>]`

## Reproducing the Bug

```python
import troposphere.forecast as forecast

attrs = [forecast.AttributesItems(AttributeName="attr1", AttributeType="string")]

schema = forecast.Schema(Attributes=attrs)

print(f"Before: {len(schema.to_dict()['Attributes'])} attributes")

attrs.append(forecast.AttributesItems(AttributeName="attr2", AttributeType="integer"))

print(f"After: {len(schema.to_dict()['Attributes'])} attributes")
```

## Why This Is A Bug

This violates the principle of encapsulation - objects should not be affected by external modifications to data structures used during their construction. This can lead to unexpected behavior where:
1. Multiple Schema objects sharing the same attributes list will all be affected by mutations
2. Code that modifies lists for reuse can unintentionally alter existing Schema objects
3. The behavior is inconsistent with user expectations of object immutability after creation

## Fix

The Schema class (and other similar classes) should create a copy of mutable arguments during initialization. Here's the fix for the BaseAWSObject class in troposphere/__init__.py:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -275,6 +275,9 @@ class BaseAWSObject:
             # If it's a list of types, check against those types...
             elif isinstance(expected_type, list):
                 # If we're expecting a list, then make sure it is a list
                 if not isinstance(value, list):
                     self._raise_type(name, value, expected_type)
+                
+                # Create a copy of the list to prevent external mutations
+                value = list(value)
 
                 # Special case a list of validation function
                 if len(expected_type) == 1 and isinstance(
```