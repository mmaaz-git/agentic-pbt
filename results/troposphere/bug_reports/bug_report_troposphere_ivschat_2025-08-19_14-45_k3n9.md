# Bug Report: troposphere.validators.integer OverflowError with Infinity Values

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `integer` validator function raises `OverflowError` instead of `ValueError` when given infinity values, causing inconsistent error handling.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf'))
))
def test_integer_validator_rejects_infinity(value):
    """Test that integer validator properly rejects infinity values."""
    with pytest.raises(ValueError):
        integer(value)
```

**Failing input**: `float('inf')` and `float('-inf')`

## Reproducing the Bug

```python
import sys
import types

sys.modules['cfn_flip'] = types.ModuleType('cfn_flip')
sys.path.insert(0, '/root/hypothesis-llm/worker_/1/troposphere-4.9.3')

from troposphere.validators import integer

try:
    result = integer(float('inf'))
except OverflowError as e:
    print(f"BUG: OverflowError raised: {e}")
except ValueError as e:
    print(f"Expected: ValueError raised: {e}")
```

## Why This Is A Bug

The `integer` validator is designed to validate integer inputs and raise `ValueError` for invalid inputs. However, it only catches `ValueError` and `TypeError` when calling `int(x)`, missing `OverflowError` that occurs with infinity values. This creates inconsistent error handling where most invalid inputs raise `ValueError` but infinity raises `OverflowError`, breaking user error handling code that expects `ValueError`.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -46,7 +46,7 @@ def boolean(x: Any) -> bool:
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```