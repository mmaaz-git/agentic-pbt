# Bug Report: django.urls.converters Inconsistent to_url() Return Types

**Target**: `django.urls.converters`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

StringConverter, SlugConverter, and PathConverter's `to_url()` methods do not convert non-string inputs to strings, returning them unchanged, while IntConverter and UUIDConverter correctly convert to strings.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from django.urls.converters import StringConverter, SlugConverter, PathConverter

@given(st.one_of(st.integers(), st.booleans(), st.floats()))
def test_converter_to_url_returns_string(value):
    """Test that all converters' to_url methods return strings"""
    converters = [StringConverter(), SlugConverter(), PathConverter()]
    
    for conv in converters:
        result = conv.to_url(value)
        assert isinstance(result, str), f"{conv.__class__.__name__}.to_url({value!r}) returned {type(result)}, expected str"
```

**Failing input**: `0` (or any non-string value)

## Reproducing the Bug

```python
from django.urls.converters import StringConverter, SlugConverter, PathConverter, IntConverter

# These converters incorrectly return non-string values unchanged
str_conv = StringConverter()
slug_conv = SlugConverter()
path_conv = PathConverter()

# These converters correctly convert to string
int_conv = IntConverter()

# Demonstration of the bug
print(f"StringConverter.to_url(42) = {str_conv.to_url(42)!r}")  # Returns: 42 (int)
print(f"SlugConverter.to_url(42) = {slug_conv.to_url(42)!r}")   # Returns: 42 (int)
print(f"PathConverter.to_url(42) = {path_conv.to_url(42)!r}")   # Returns: 42 (int)
print(f"IntConverter.to_url(42) = {int_conv.to_url(42)!r}")     # Returns: '42' (str)

# The issue occurs with any non-string type
print(f"StringConverter.to_url(True) = {str_conv.to_url(True)!r}")  # Returns: True (bool)
```

## Why This Is A Bug

The `to_url()` method is meant to convert Python values to their URL string representation. All converters should consistently return strings from this method, as URLs are inherently text-based. The current inconsistent behavior can lead to:

1. Type errors when the returned value is used in string operations
2. Inconsistent behavior across different converter types
3. Violations of the implicit contract that `to_url()` produces URL-safe strings

## Fix

```diff
--- a/django/urls/converters.py
+++ b/django/urls/converters.py
@@ -14,7 +14,7 @@ class StringConverter:
         return value
 
     def to_url(self, value):
-        return value
+        return str(value)
 
 
 class IntConverter:
@@ -34,7 +34,7 @@ class SlugConverter:
         return value
 
     def to_url(self, value):
-        return value
+        return str(value)
 
 
 class PathConverter:
@@ -45,7 +45,7 @@ class PathConverter:
         return value
 
     def to_url(self, value):
-        return value
+        return str(value)
```