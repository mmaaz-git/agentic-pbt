# Bug Report: addict.Dict Union Operators Violate Standard Dict Semantics

**Target**: `addict.Dict`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The Dict class's union operators (| and |=) violate Python's standard dict union semantics by recursively merging nested dicts instead of replacing them.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from addict import Dict

@given(nested_dicts(), nested_dicts())
def test_dict_union_operator(data1, data2):
    """Property: Dict union (|) should combine dicts correctly"""
    d1 = Dict(data1)
    d2 = Dict(data2)
    
    d3 = d1 | d2
    
    for key in d2:
        assert d3[key] == d2[key]  # d2 values should override d1
```

**Failing input**: `data1={0: {0: None}}, data2={0: {}}`

## Reproducing the Bug

```python
from addict import Dict

data1 = {0: {0: None}}
data2 = {0: {}}

d1 = Dict(data1)
d2 = Dict(data2)

result = d1 | d2
print(f"d1 | d2 = {result}")
print(f"Expected: {data2}")
print(f"Got: {dict(result)}")

std_result = dict(data1) | dict(data2)
print(f"Standard dict union: {std_result}")
```

## Why This Is A Bug

Python's dict union operator (|) performs simple replacement: when keys overlap, the right operand's value completely replaces the left operand's value. However, addict.Dict's implementation uses its custom update() method which recursively merges nested dicts. This violates the expected contract:

- Standard dict: `{'a': {'b': 1}} | {'a': {'c': 2}}` → `{'a': {'c': 2}}`
- addict.Dict: `{'a': {'b': 1}} | {'a': {'c': 2}}` → `{'a': {'b': 1, 'c': 2}}`

This behavior is inconsistent with Python's dict API contract that Dict claims to extend.

## Fix

```diff
--- a/addict.py
+++ b/addict.py
@@ -127,8 +127,15 @@ class Dict(dict):
     def __or__(self, other):
         if not isinstance(other, (Dict, dict)):
             return NotImplemented
         new = Dict(self)
-        new.update(other)
+        # Use standard dict union semantics: simple replacement, not recursive merge
+        for k, v in other.items():
+            new[k] = v
         return new
 
     def __ior__(self, other):
-        self.update(other)
+        if not isinstance(other, (Dict, dict)):
+            return NotImplemented
+        # Use standard dict union semantics: simple replacement, not recursive merge
+        for k, v in other.items():
+            self[k] = v
         return self
```