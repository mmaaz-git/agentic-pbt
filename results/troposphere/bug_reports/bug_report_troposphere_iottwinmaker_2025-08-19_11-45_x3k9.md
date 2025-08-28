# Bug Report: troposphere.iottwinmaker Validators Return None

**Target**: `troposphere.iottwinmaker`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The validators `validate_listvalue` and `validate_nestedtypel` in troposphere.iottwinmaker don't return the validated values, causing DataValue.ListValue and DataType.NestedType properties to always be None.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import iottwinmaker

@given(
    string_val1=st.text(min_size=1),
    string_val2=st.text(min_size=1)
)
def test_datavalue_listvalue(string_val1, string_val2):
    # Create DataValues for the list
    dv1 = iottwinmaker.DataValue(StringValue=string_val1)
    dv2 = iottwinmaker.DataValue(StringValue=string_val2)
    
    # Create DataValue with ListValue
    dv_list = iottwinmaker.DataValue(ListValue=[dv1, dv2])
    
    # ListValue should be preserved in to_dict()
    result = dv_list.to_dict()
    assert result["ListValue"] is not None  # FAILS - ListValue is None!
    assert len(result["ListValue"]) == 2
```

**Failing input**: Any valid input fails (e.g., string_val1="test", string_val2="test2")

## Reproducing the Bug

```python
from troposphere import iottwinmaker

# Bug 1: DataValue.ListValue returns None
dv1 = iottwinmaker.DataValue(StringValue="test")
dv2 = iottwinmaker.DataValue(IntegerValue=42)
dv_list = iottwinmaker.DataValue(ListValue=[dv1, dv2])

result = dv_list.to_dict()
print(result)  # {'ListValue': None} - BUG!

# Bug 2: DataType.NestedType returns None  
inner_dt = iottwinmaker.DataType(Type="STRING")
outer_dt = iottwinmaker.DataType(NestedType=inner_dt)

result = outer_dt.to_dict()
print(result)  # {'NestedType': None} - BUG!
```

## Why This Is A Bug

The validators `validate_listvalue` and `validate_nestedtypel` are used as property validators in troposphere. When a validator function is used, troposphere expects it to return the validated value. However, these two validators only perform type checking and raise exceptions on invalid input, but don't return anything. In Python, functions without explicit return statements return None by default. This causes the properties to be set to None instead of the actual validated values.

## Fix

```diff
--- a/troposphere/validators/iottwinmaker.py
+++ b/troposphere/validators/iottwinmaker.py
@@ -21,6 +21,7 @@ def validate_listvalue(values):
                 AWSHelperFn,
                 DataValue,
             )
+    return values
 
 
 def validate_nestedtypel(value):
@@ -34,3 +35,4 @@ def validate_nestedtypel(value):
         raise TypeError(
             "NestedType must be either DataType or AWSHelperFn", AWSHelperFn, DataType
         )
+    return value
```