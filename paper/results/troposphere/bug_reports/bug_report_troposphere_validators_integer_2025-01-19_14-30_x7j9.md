# Bug Report: troposphere.validators.integer Returns Wrong Type

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-19

## Summary

The `integer()` validator function returns the original input type instead of converting it to an integer, causing float values to pass through unconverted when they should be converted to integers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(
    weight=st.floats(allow_nan=False, allow_infinity=False)
)
def test_integer_validator_returns_int(weight):
    """Test that integer validator returns int type."""
    try:
        validated = integer(weight)
        assert isinstance(validated, int), f"Expected int, got {type(validated)}"
    except ValueError:
        pass  # Should raise for non-convertible values
```

**Failing input**: `0.0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import troposphere.lex as lex
import json

# Bug 1: integer() returns float instead of int
result = integer(5.0)
print(f"integer(5.0) = {result}, type = {type(result)}")
assert isinstance(result, float)  # BUG: Should be int

# Bug 2: This causes incorrect types in CloudFormation resources
item = lex.CustomVocabularyItem(Phrase="test")
item.properties['Weight'] = integer(5.0)
print(f"Weight = {item.properties['Weight']}, type = {type(item.properties['Weight'])}")

# Bug 3: JSON serialization includes .0 suffix where integers expected  
json_output = json.dumps(item.to_dict())
print(f"JSON: {json_output}")
assert '"Weight": 5.0' in json_output  # Should be "Weight": 5
```

## Why This Is A Bug

The `integer()` validator is meant to validate and convert values to integers. However, it only validates that the input can be converted to int but returns the original value unchanged. This violates the expected contract of a type validator and causes downstream issues with CloudFormation templates expecting integer types.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,7 +46,7 @@ def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
         int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
-        return x
+        return int(x)
```