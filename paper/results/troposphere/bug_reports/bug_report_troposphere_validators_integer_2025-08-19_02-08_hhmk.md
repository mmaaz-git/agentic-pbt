# Bug Report: troposphere.validators.integer OverflowError on Infinity

**Target**: `troposphere.validators.integer`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `integer()` validator function crashes with OverflowError when given float infinity values instead of raising the expected ValueError.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import integer

@given(
    st.one_of(
        st.integers(),
        st.text(),
        st.floats(),
        st.none(),
        st.lists(st.integers())
    )
)
def test_integer_validator(value):
    """Test that integer validator accepts valid integers and rejects invalid ones"""
    try:
        result = integer(value)
        # If it succeeds, we should be able to convert result to int
        int_val = int(result)
        # And converting the original value should give the same result
        assert int(value) == int_val
    except (ValueError, TypeError):
        # Should fail for non-integer-convertible values
        # Verify that it indeed cannot be converted to int
        try:
            int(value)
            # If we can convert it, the validator should have accepted it
            assert False, f"integer() rejected {value} but int() accepts it"
        except (ValueError, TypeError):
            # Expected - both should fail
            pass
```

**Failing input**: `inf`

## Reproducing the Bug

```python
from troposphere.validators import integer

# This should raise ValueError but raises OverflowError instead
try:
    result = integer(float('inf'))
except ValueError:
    print("ValueError raised as expected")
except OverflowError as e:
    print(f"BUG: OverflowError raised: {e}")

# Same issue with negative infinity
try:
    result = integer(float('-inf'))
except ValueError:
    print("ValueError raised as expected")
except OverflowError as e:
    print(f"BUG: OverflowError raised: {e}")
```

## Why This Is A Bug

The `integer()` validator is documented to raise ValueError for invalid inputs. Float infinity values cannot be converted to integers and should trigger a ValueError like other invalid inputs (e.g., NaN, strings, None). Instead, the function allows the OverflowError from `int()` to propagate, violating the expected exception contract.

## Fix

```diff
--- a/troposphere/validators/__init__.py
+++ b/troposphere/validators/__init__.py
@@ -45,7 +45,10 @@ def boolean(x: Any) -> bool:
 
 def integer(x: Any) -> Union[str, bytes, SupportsInt, SupportsIndex]:
     try:
-        int(x)
+        import math
+        if isinstance(x, float) and math.isinf(x):
+            raise ValueError("%r is not a valid integer" % x)
+        int(x)
     except (ValueError, TypeError):
         raise ValueError("%r is not a valid integer" % x)
     else:
```