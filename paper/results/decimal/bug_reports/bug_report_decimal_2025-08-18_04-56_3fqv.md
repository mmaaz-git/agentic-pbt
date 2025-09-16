# Bug Report: decimal Modulo Operator Inconsistent with Python Integer Modulo

**Target**: `decimal.Decimal.__mod__`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The modulo operator (%) for `decimal.Decimal` uses truncated division semantics, while Python's built-in integer modulo uses Euclidean division semantics, leading to different results for negative operands.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import decimal

@given(st.integers(-100, 100), st.integers(-100, 100))
def test_modulo_consistency(a, b):
    """Test that Decimal modulo matches Python integer modulo"""
    if b == 0:
        return  # Skip division by zero
    
    int_result = a % b
    decimal_result = int(decimal.Decimal(a) % decimal.Decimal(b))
    
    assert int_result == decimal_result, \
        f"Modulo mismatch: {a} % {b} = {int_result} (int) vs {decimal_result} (Decimal)"
```

**Failing input**: `a=-1, b=2`

## Reproducing the Bug

```python
import decimal

a, b = -1, 2

int_modulo = a % b
decimal_modulo = decimal.Decimal(a) % decimal.Decimal(b)

print(f"Python int: {a} % {b} = {int_modulo}")
print(f"Decimal:    {a} % {b} = {decimal_modulo}")
print(f"Match: {int_modulo == decimal_modulo}")

int_divmod = divmod(a, b)
decimal_divmod = divmod(decimal.Decimal(a), decimal.Decimal(b))

print(f"\nPython divmod({a}, {b}) = {int_divmod}")
print(f"Decimal divmod({a}, {b}) = {decimal_divmod}")
```

## Why This Is A Bug

This violates the principle of least surprise. Users expect consistent mathematical operations across numeric types in Python. The difference arises from:

1. **Python integers** use Euclidean division: the remainder has the same sign as the divisor
2. **Decimal** uses truncated division: the remainder has the same sign as the dividend

This inconsistency can lead to subtle bugs when switching between integer and Decimal arithmetic, particularly in financial calculations where sign matters.

## Fix

The fix would require changing `Decimal.__mod__` to match Python's integer semantics. However, this may break backward compatibility as the current behavior follows the IBM General Decimal Arithmetic Specification. A possible solution is to provide a flag or alternative method for Python-compatible modulo:

```diff
# Conceptual fix - add a method for Python-compatible modulo
+ def python_mod(self, other):
+     """Return self modulo other using Python integer semantics."""
+     result = self % other
+     if (result != 0) and ((result < 0) != (other < 0)):
+         result += other
+     return result
```

Alternatively, document this difference prominently in the module documentation to prevent user confusion.