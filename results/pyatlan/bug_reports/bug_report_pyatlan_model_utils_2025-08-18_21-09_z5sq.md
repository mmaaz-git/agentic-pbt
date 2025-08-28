# Bug Report: pyatlan.model.utils to_python_class_name Returns Invalid Class Names

**Target**: `pyatlan.model.utils.to_python_class_name`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `to_python_class_name` function fails to handle Python keywords and doesn't properly capitalize after removing leading digits, producing invalid Python class names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import keyword
from pyatlan.model.utils import to_python_class_name

@given(st.text())
def test_to_python_class_name_always_valid(s):
    result = to_python_class_name(s)
    
    if result:
        assert result.isidentifier(), f"'{result}' is not a valid identifier"
        assert not keyword.iskeyword(result), f"'{result}' is a Python keyword"
        assert result[0].isupper(), f"'{result}' doesn't start with uppercase"
```

**Failing input**: `'None'` and `'0A'`

## Reproducing the Bug

```python
from pyatlan.model.utils import to_python_class_name
import keyword

result1 = to_python_class_name('None')
print(f"Input: 'None' -> Output: '{result1}'")
print(f"Is keyword: {keyword.iskeyword(result1)}")  # True - BUG!

result2 = to_python_class_name('0A')
print(f"Input: '0A' -> Output: '{result2}'")
print(f"Starts with uppercase: {result2[0].isupper()}")  # False - BUG!
```

## Why This Is A Bug

The function's docstring explicitly states it should "Convert any string to a valid Python class name following PEP 8 conventions." However:

1. It returns Python keywords ('None', 'True', 'False') unchanged, violating the requirement that class names cannot be keywords
2. After removing leading digits, it returns lowercase-starting strings ('a' from '0A'), violating PEP 8 convention that class names start with uppercase

## Fix

```diff
--- a/pyatlan/model/utils.py
+++ b/pyatlan/model/utils.py
@@ -96,7 +96,7 @@ def is_valid_python_class_name(string):
         if keyword.iskeyword(string):
             return False
 
         # Check if it starts with capital letter (PEP 8 convention for classes)
         if not string[0].isupper():
             return False
 
@@ -108,10 +108,13 @@ def to_python_class_name(string):
     if not string:
         return ""
 
     # If it's already a valid class name, return as is
-    if is_valid_python_class_name(string):
+    # But still need to check for keywords since the valid check doesn't
+    if is_valid_python_class_name(string) and not keyword.iskeyword(string):
         return string
+    elif is_valid_python_class_name(string) and keyword.iskeyword(string):
+        return string + "_"
 
     # Check if it's a valid identifier but needs conversion from snake_case
     if string.isidentifier() and not keyword.iskeyword(string):
         # If it contains underscores, convert from snake_case to PascalCase
@@ -144,8 +147,11 @@ def to_python_class_name(string):
     if class_name and class_name[0].isdigit():
         # Remove leading digits
         class_name = re.sub(r"^\d+", "", class_name)
         if not class_name:
             return ""
+        # Ensure first character is uppercase after removing digits
+        if class_name and class_name[0].islower():
+            class_name = class_name[0].upper() + class_name[1:]
 
     # Handle Python keywords
     if keyword.iskeyword(class_name.lower()):
         class_name += "_"
```