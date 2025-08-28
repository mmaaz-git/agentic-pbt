# Bug Report: pyatlan.model.utils.to_python_class_name Invalid Class Names

**Target**: `pyatlan.model.utils.to_python_class_name`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `to_python_class_name` function violates its documented contract by returning invalid Python class names in two scenarios: returning lowercase-starting identifiers and returning Python keywords.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import keyword

@given(st.text())
def test_to_python_class_name_returns_valid_or_empty(input_string):
    result = to_python_class_name(input_string)
    
    if result:
        assert result.isidentifier(), f"{result} is not a valid identifier"
        assert not keyword.iskeyword(result), f"{result} is a Python keyword"
        assert result[0].isupper(), f"{result} doesn't start with uppercase"

@given(st.text())
def test_to_python_class_name_never_invalid(input_string):
    result = to_python_class_name(input_string)
    
    if result:
        try:
            exec(f"class {result}: pass")
        except SyntaxError:
            assert False, f"to_python_class_name returned invalid class name: {result}"
```

**Failing input**: `'0A'` and `'none'`

## Reproducing the Bug

```python
from pyatlan.model.utils import to_python_class_name

result1 = to_python_class_name('0A')
print(f"to_python_class_name('0A') = '{result1}'")
print(f"Starts with uppercase? {result1[0].isupper()}")

result2 = to_python_class_name('none')
print(f"to_python_class_name('none') = '{result2}'")
try:
    exec(f"class {result2}: pass")
    print("Can be used as class name: Yes")
except SyntaxError:
    print("Can be used as class name: No")
```

## Why This Is A Bug

The function's docstring states it should "Convert any string to a valid Python class name following PEP 8 conventions" and return either a valid class name or empty string. However:

1. Input `'0A'` returns `'a'` which violates PEP 8 (class names should start with uppercase)
2. Input `'none'` returns `'None'` which is a Python keyword and cannot be used as a class name

## Fix

```diff
@@ -143,7 +143,11 @@ def to_python_class_name(string):
     # Ensure it doesn't start with a digit
     if class_name and class_name[0].isdigit():
         # Remove leading digits
         class_name = re.sub(r"^\d+", "", class_name)
         if not class_name:
             return ""
+        # Ensure first character is uppercase after removing digits
+        if class_name and not class_name[0].isupper():
+            class_name = class_name[0].upper() + class_name[1:]
 
     # Handle Python keywords
-    if keyword.iskeyword(class_name.lower()):
+    # Check both the actual class name and its lowercase version
+    if keyword.iskeyword(class_name) or keyword.iskeyword(class_name.lower()):
         class_name += "_"
 
     return class_name
```