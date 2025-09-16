# Bug Report: sqlalchemy.types.Float Precision Loss During Decimal Conversion

**Target**: `sqlalchemy.types.Float`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The Float type in SQLAlchemy loses precision when converting float values to Decimal with `asdecimal=True`, due to string formatting with a fixed number of decimal places.

## Property-Based Test

```python
from decimal import Decimal
from hypothesis import given, strategies as st
import sqlalchemy.types as types

@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e20, max_value=1e20))
def test_float_to_decimal_precision_property(value):
    ft = types.Float(asdecimal=True, decimal_return_scale=10)
    
    class MockDialect:
        supports_native_decimal = False
    
    dialect = MockDialect()
    result_proc = ft.result_processor(dialect, None)
    
    if result_proc and value is not None:
        retrieved = result_proc(value)
        expected = Decimal(str(value))
        
        if float(expected) == value and float(retrieved) != value:
            assert float(retrieved) == value, f"Precision lost for {value}"
```

**Failing input**: `7.357134066239441e-19`

## Reproducing the Bug

```python
from decimal import Decimal
import sqlalchemy.types as types

original_float = 7.357134066239441e-19

ft = types.Float(asdecimal=True, decimal_return_scale=10)

class MockDialect:
    supports_native_decimal = False

dialect = MockDialect()
result_proc = ft.result_processor(dialect, None)

retrieved_decimal = result_proc(original_float)

print(f"Original:  {original_float}")
print(f"Retrieved: {retrieved_decimal}")
print(f"Back to float: {float(retrieved_decimal)}")

assert float(retrieved_decimal) == original_float
```

## Why This Is A Bug

The Float type's result processor uses string formatting (`"%.10f" % value`) to convert floats to Decimal, which truncates values to a fixed number of decimal places. This causes complete loss of very small values (they become 0) and precision loss for values with more significant digits than the scale parameter. The correct approach would be to convert the float directly to string then to Decimal, preserving all available precision.

## Fix

```diff
--- a/sqlalchemy/engine/_py_processors.py
+++ b/sqlalchemy/engine/_py_processors.py
@@ -80,13 +80,10 @@ def str_to_datetime_processor_factory(
 def to_decimal_processor_factory(
     target_class: Type[Decimal], scale: int
 ) -> Callable[[Optional[float]], Optional[Decimal]]:
-    fstring = "%%.%df" % scale
-
     def process(value: Optional[float]) -> Optional[Decimal]:
         if value is None:
             return None
         else:
-            return target_class(fstring % value)
+            return target_class(str(value))
 
     return process
```