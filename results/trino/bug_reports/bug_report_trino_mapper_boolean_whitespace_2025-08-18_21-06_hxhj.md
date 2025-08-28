# Bug Report: trino.mapper.BooleanValueMapper Fails on Strings with Whitespace

**Target**: `trino.mapper.BooleanValueMapper`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

BooleanValueMapper fails to parse boolean string values that contain leading or trailing whitespace, even though such values commonly occur in real-world data transmission scenarios.

## Property-Based Test

```python
from hypothesis import given, strategies as st, example
from trino.mapper import BooleanValueMapper
import pytest

@given(st.text().filter(lambda x: x.lower() not in ['true', 'false']))
@example("TRUE ")  # trailing space
@example(" TRUE")  # leading space
def test_boolean_invalid_strings(value):
    """BooleanValueMapper should handle whitespace in boolean strings."""
    mapper = BooleanValueMapper()
    if value.strip().lower() in ['true', 'false']:
        # These should work after stripping
        result = mapper.map(value)
        assert isinstance(result, bool)
    else:
        with pytest.raises(ValueError):
            mapper.map(value)
```

**Failing input**: `'TRUE '` and `' TRUE'`

## Reproducing the Bug

```python
from trino.mapper import BooleanValueMapper

mapper = BooleanValueMapper()

# These should return True but raise ValueError instead
try:
    result = mapper.map('TRUE ')
    print(f"'TRUE ' -> {result}")
except ValueError as e:
    print(f"'TRUE ' raises: {e}")

try:
    result = mapper.map(' TRUE')
    print(f"' TRUE' -> {result}")  
except ValueError as e:
    print(f"' TRUE' raises: {e}")
```

## Why This Is A Bug

The mapper correctly handles 'true' and 'TRUE' but fails on 'TRUE ' and ' TRUE'. In real-world scenarios, data from servers and databases often contains whitespace padding. The mapper should either strip whitespace before checking or document that whitespace is not tolerated.

## Fix

```diff
--- a/trino/mapper.py
+++ b/trino/mapper.py
@@ -44,10 +44,11 @@ class BooleanValueMapper(ValueMapper[bool]):
             return None
         if isinstance(value, bool):
             return value
-        if str(value).lower() == 'true':
+        str_value = str(value).strip()
+        if str_value.lower() == 'true':
             return True
-        if str(value).lower() == 'false':
+        if str_value.lower() == 'false':
             return False
         raise ValueError(f"Server sent unexpected value {value} of type {type(value)} for boolean")
```