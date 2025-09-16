# Bug Report: sqlalchemy.sql not_ operator fails to simplify Python booleans

**Target**: `sqlalchemy.sql.not_`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `sql.not_()` function fails to simplify Python boolean values (True/False) to SQL constants, instead creating parameter bindings that prevent proper logical simplification in compound expressions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sqlalchemy.sql as sql

@given(st.booleans(), st.booleans(), st.booleans())
def test_mixed_logical_ops(a, b, c):
    """Test mixing and_, or_, not_ with Python booleans."""
    result = sql.or_(sql.and_(a, b), sql.not_(c))
    result_str = str(result)
    
    # Verify logical evaluation matches Python
    python_result = (a and b) or (not c)
    
    if python_result:
        assert result_str == 'true' or 'true' in result_str.lower()
    else:
        assert result_str == 'false'
```

**Failing input**: `a=False, b=False, c=False`

## Reproducing the Bug

```python
import sqlalchemy.sql as sql

# Bug: not_(False) should simplify to 'true' but creates parameter
result = sql.not_(False)
print(f"sql.not_(False): {str(result)}")  # Output: NOT :param_1

# This breaks logical simplification
expr = sql.or_(sql.false(), sql.not_(False))  
print(f"sql.or_(sql.false(), sql.not_(False)): {str(expr)}")  # Output: NOT :param_1
# Expected: 'true' (since false OR true = true)

# Workaround: using SQL constants works correctly
correct = sql.or_(sql.false(), sql.not_(sql.false()))
print(f"sql.or_(sql.false(), sql.not_(sql.false())): {str(correct)}")  # Output: true
```

## Why This Is A Bug

SQLAlchemy's logical operators are designed to simplify boolean expressions. The `and_()` and `or_()` functions correctly simplify Python booleans to SQL constants ('true'/'false'), but `not_()` doesn't apply the same simplification. This inconsistency causes:

1. Incorrect logical simplification in compound expressions
2. Generated SQL contains unnecessary parameter bindings
3. Logical expressions don't evaluate as expected when mixing Python booleans with SQL expressions

## Fix

The `not_()` function should check if its argument is a Python boolean and convert it to the appropriate SQL constant before applying negation:

```diff
# In sqlalchemy/sql/_elements_constructors.py or similar location
def not_(clause):
+   # Convert Python booleans to SQL constants
+   if clause is True:
+       clause = true()
+   elif clause is False:
+       clause = false()
    
    # Apply negation (existing logic)
    return clause._negate()
```

This would ensure consistent behavior across all logical operators and proper simplification of boolean expressions.