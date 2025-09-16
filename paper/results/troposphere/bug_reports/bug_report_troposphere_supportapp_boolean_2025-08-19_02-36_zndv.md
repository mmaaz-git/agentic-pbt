# Bug Report: troposphere.supportapp.boolean Accepts Unintended Numeric Types

**Target**: `troposphere.supportapp.boolean`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `boolean` function accepts any numeric type that equals 1 or 0 (floats, complex numbers, Decimals, numpy types) despite the implementation explicitly listing only `[True, 1, "1", "true", "True"]` and `[False, 0, "0", "false", "False"]`.

## Property-Based Test

```python
@given(st.one_of(
    st.floats(min_value=0.99, max_value=1.01),
    st.decimals(min_value=Decimal('0.99'), max_value=Decimal('1.01')),
    st.complex_numbers(max_magnitude=2)
))
def test_numeric_type_equality_loophole(x):
    """Test that any numeric type equal to 1 or 0 is accepted, not just int."""
    if x == 1:
        assert mod.boolean(x) is True
    elif x == 0:
        assert mod.boolean(x) is False
    else:
        with pytest.raises(ValueError):
            mod.boolean(x)
```

**Failing input**: `1.0`, `0.0`, `complex(1, 0)`, `Decimal('1')`, etc.

## Reproducing the Bug

```python
import troposphere.supportapp as mod
from decimal import Decimal

# These should raise ValueError but don't:
assert mod.boolean(1.0) is True          # float not in list
assert mod.boolean(0.0) is False         # float not in list  
assert mod.boolean(complex(1, 0)) is True  # complex definitely not intended
assert mod.boolean(Decimal('1')) is True   # Decimal not in list

# But string representations correctly raise ValueError:
try:
    mod.boolean("1.0")  # Correctly raises ValueError
except ValueError:
    pass

print("Bug reproduced: Unintended numeric types accepted")
```

## Why This Is A Bug

The function's implementation explicitly checks `if x in [True, 1, "1", "true", "True"]` but Python's `in` operator uses `==` for comparison. This causes any object that compares equal to 1 or 0 to be accepted, including float, complex, Decimal, and numpy types. This violates the clear intent to accept only specific types.

## Fix

```diff
def boolean(x: Any) -> bool:
-    if x in [True, 1, "1", "true", "True"]:
+    if x is True or x == 1 and type(x) is int or x in ["1", "true", "True"]:
         return True
-    if x in [False, 0, "0", "false", "False"]:
+    if x is False or x == 0 and type(x) is int or x in ["0", "false", "False"]:
         return False
     raise ValueError
```