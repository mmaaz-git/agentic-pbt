# Bug Report: troposphere.ssmincidents Type Handling Issues

**Target**: `troposphere.ssmincidents`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Found multiple type handling inconsistencies in troposphere.ssmincidents: integer() function returns strings instead of integers, boolean() function has case sensitivity issues, and Impact field preserves incorrect types.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ssmincidents as ssmincidents
import pytest

@given(st.text(alphabet='0123456789', min_size=1))
def test_integer_function_type_preservation(value):
    result = ssmincidents.integer(value)
    assert isinstance(result, int), f"integer('{value}') returned {type(result).__name__} instead of int"

@given(st.sampled_from(['TRUE', 'FALSE']))  
def test_boolean_case_sensitivity(text):
    lower_result = ssmincidents.boolean(text.lower())
    try:
        upper_result = ssmincidents.boolean(text)
        assert upper_result == lower_result
    except ValueError:
        pytest.fail(f"boolean('{text}') failed but boolean('{text.lower()}') succeeded")

@given(st.integers(min_value=1, max_value=5))
def test_impact_field_type_consistency(impact):
    template1 = ssmincidents.IncidentTemplate(Title='Test', Impact=impact)
    template2 = ssmincidents.IncidentTemplate(Title='Test', Impact=str(impact))
    dict1 = template1.to_dict()
    dict2 = template2.to_dict()
    assert dict1['Impact'] == dict2['Impact'], f"Impact type inconsistency: {type(dict1['Impact'])} vs {type(dict2['Impact'])}"
```

**Failing input**: `'0'` for integer test, `'TRUE'` for boolean test, `1` vs `'1'` for Impact test

## Reproducing the Bug

```python
import troposphere.ssmincidents as ssmincidents

# Bug 1: integer() returns string instead of int
result = ssmincidents.integer('123')
assert isinstance(result, str)  # Should be int!
print(f"integer('123') = {repr(result)} (type: {type(result).__name__})")

# Bug 2: boolean() case sensitivity  
try:
    ssmincidents.boolean('TRUE')
    print("boolean('TRUE') succeeded")
except ValueError:
    print("boolean('TRUE') failed - case sensitivity issue")

# Bug 3: Type inconsistency in Impact field
template1 = ssmincidents.IncidentTemplate(Title='Test', Impact=3)
template2 = ssmincidents.IncidentTemplate(Title='Test', Impact='3')
dict1 = template1.to_dict()
dict2 = template2.to_dict()
print(f"Impact=3: {repr(dict1['Impact'])} (type: {type(dict1['Impact']).__name__})")
print(f"Impact='3': {repr(dict2['Impact'])} (type: {type(dict2['Impact']).__name__})")
print(f"Equal? {dict1['Impact'] == dict2['Impact']}")
```

## Why This Is A Bug

1. **integer() function**: Accepts string representations of integers but returns them as strings instead of converting to int type. This violates the expected contract of a function named "integer" which should ensure integer type.

2. **boolean() function**: Accepts 'True'/'False' but not 'TRUE'/'FALSE', showing inconsistent case handling. Most boolean parsers are case-insensitive for better usability.

3. **Impact field**: When Impact is set with a string like '3', it remains a string in the output dict instead of being converted to integer. This causes type inconsistency where the same logical value has different types depending on input format.

These issues can cause problems in downstream code that expects consistent types, especially when serializing to JSON or comparing values.

## Fix

```diff
# For integer() function in troposphere/validators/__init__.py
def integer(x):
    if isinstance(x, str):
        try:
-           int(x)  # Just validates, doesn't convert
-           return x
+           return int(x)  # Convert and return
        except ValueError:
            raise ValueError(f"'{x}' is not a valid integer")
    # ... rest of function

# For boolean() function in troposphere/validators/__init__.py  
def boolean(x):
-   if x in [True, 1, "1", "true", "True"]:
+   if x in [True, 1, "1"] or (isinstance(x, str) and x.lower() == "true"):
        return True
-   if x in [False, 0, "0", "false", "False"]:
+   if x in [False, 0, "0"] or (isinstance(x, str) and x.lower() == "false"):
        return False
    raise ValueError
```