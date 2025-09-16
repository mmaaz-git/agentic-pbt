# Bug Report: troposphere.rekognition boolean Function Doesn't Handle 'TRUE'

**Target**: `troposphere.rekognition.boolean`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `boolean` function raises ValueError for 'TRUE' (all caps) while accepting 'True' and 'true', creating inconsistent case handling.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.rekognition as rek

@given(st.sampled_from(['true', 'false', 'True', 'False', 'TRUE', 'FALSE']))
def test_boolean_conversion(value):
    """Test that boolean function correctly converts various case inputs"""
    result = rek.boolean(value)
    assert isinstance(result, bool)
    
    if value.upper() == 'TRUE':
        assert result is True
    elif value.upper() == 'FALSE':
        assert result is False
```

**Failing input**: `'TRUE'` or `'FALSE'`

## Reproducing the Bug

```python
import troposphere.rekognition as rek

# These work
print(rek.boolean('true'))   # True
print(rek.boolean('True'))   # True

# This fails
try:
    print(rek.boolean('TRUE'))
except ValueError:
    print("ValueError: 'TRUE' not accepted")

# Same issue with FALSE
try:
    print(rek.boolean('FALSE'))
except ValueError:
    print("ValueError: 'FALSE' not accepted")
```

## Why This Is A Bug

The function accepts 'true' and 'True' but not 'TRUE', creating an inconsistent interface. Users reasonably expect all common case variations of boolean strings to be accepted.

## Fix

Add support for uppercase variants:

```diff
 def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x in [True, 1, "1", "true", "True", "TRUE"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x in [False, 0, "0", "false", "False", "FALSE"]:
         return False
     raise ValueError
```