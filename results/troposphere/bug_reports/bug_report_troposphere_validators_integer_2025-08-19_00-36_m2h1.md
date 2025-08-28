# Bug Report: troposphere.validators integer() Raises Wrong Exception Type for Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `integer()` validator function raises `OverflowError` instead of `ValueError` when given infinity values, violating its error contract that promises to raise `ValueError` for invalid inputs.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from troposphere import validators

@given(st.sampled_from([float('inf'), float('-inf')]))
def test_integer_validator_infinity_handling(value):
    """Test that integer validator properly handles infinity values."""
    # Should raise ValueError for all invalid inputs
    with pytest.raises(ValueError):
        validators.integer(value)
```

**Failing input**: `float('inf')`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

validators.integer(float('inf'))
```

## Why This Is A Bug

The `integer()` validator function is documented to raise `ValueError` for invalid inputs. At line 50 of `validators/__init__.py`, it explicitly raises `ValueError` with the message `"%r is not a valid integer"`. However, when passed infinity values, it raises `OverflowError` instead because the internal `int(x)` call at line 48 raises `OverflowError` for infinity values. This inconsistent error handling violates the function's contract and could break error handling code that expects only `ValueError`.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,7 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
         int(x)
-    except (ValueError, TypeError):
+    except (ValueError, TypeError, OverflowError):
         raise ValueError("%r is not a valid integer" % x)
     else:
         return x
```