# Bug Report: numpy.matrixlib Matrix String Parser Accepts Non-Numeric Literals

**Target**: `numpy.matrixlib.matrix`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `numpy.matrix` string parser incorrectly accepts Python literals like `None`, creating object-dtype matrices that cannot be used in mathematical operations, violating the expectation that matrices contain numeric data.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy as np

@given(st.sampled_from(['None', 'True', 'False', '{}', '[]']))
def test_matrix_string_parser_rejects_non_numeric(literal):
    """Matrix string parser should reject non-numeric literals"""
    # Create matrix with the literal
    m = np.matrix(f"{literal} 1; 2 3")
    
    # If it accepts the literal, try to use it mathematically
    m2 = np.matrix("4 5; 6 7")
    
    # This should work if matrix only contains numeric data
    result = m + m2  # Fails with TypeError for None
```

**Failing input**: `"None 1; 2 3"`

## Reproducing the Bug

```python
import numpy as np

# Create matrix with None literal
m1 = np.matrix("None 2; 3 4")
print(f"Matrix: {m1}")
print(f"dtype: {m1.dtype}")  # object dtype

# Try mathematical operations
m2 = np.matrix("5 6; 7 8")

# Both fail with TypeError
try:
    result = m1 + m2
except TypeError as e:
    print(f"Addition fails: {e}")

try:
    result = m1 * m2  
except TypeError as e:
    print(f"Multiplication fails: {e}")
```

## Why This Is A Bug

The matrix string parser uses `ast.literal_eval` which successfully parses Python literals like `None`, `True`, `False`, creating object-dtype arrays. This violates the mathematical matrix contract because:

1. Matrices are expected to contain numeric data for mathematical operations
2. No warning or error is raised when creating non-numeric matrices from strings
3. The resulting matrices fail on basic operations like addition and multiplication
4. Users likely intend numeric input, not Python object literals

## Fix

```diff
--- a/numpy/matrixlib/defmatrix.py
+++ b/numpy/matrixlib/defmatrix.py
@@ -24,7 +24,13 @@ def _convert_from_string(data):
         newrow = []
         for col in trow:
             temp = col.split()
-            newrow.extend(map(ast.literal_eval, temp))
+            for item in temp:
+                val = ast.literal_eval(item)
+                # Reject non-numeric literals
+                if val is None or isinstance(val, (dict, list, tuple, set)):
+                    raise ValueError(f"Non-numeric literal '{item}' not allowed in matrix string")
+                newrow.append(val)
         if count == 0:
             Ncols = len(newrow)
         elif len(newrow) != Ncols:
```