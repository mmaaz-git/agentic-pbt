# Bug Report: awkward.forms Index Type Validation Mismatch

**Target**: `awkward.forms` - Multiple form classes
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Multiple Form classes accept index types during construction that their corresponding Array implementations do not support, leading to TypeError crashes when creating arrays via `length_zero_array()` or `length_one_array()`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import awkward.forms as forms

@given(st.sampled_from(["i8", "u8"]))
def test_bitmasked_form_index_types(index_type):
    form = forms.BitMaskedForm(index_type, forms.NumpyForm('bool'), valid_when=True, lsb_order=False)
    arr = form.length_zero_array()
    assert len(arr) == 0
    
@given(st.sampled_from(["i8", "u8"]))  
def test_indexed_form_index_types(index_type):
    form = forms.IndexedForm(index_type, forms.NumpyForm('bool'))
    arr = form.length_zero_array()
    assert len(arr) == 0
```

**Failing inputs**: 
- `BitMaskedForm('i8', ...)` - expects uint8
- `ByteMaskedForm('i8', ...)` - expects uint8  
- `IndexedForm('i8', ...)` - expects int32/uint32/int64
- `IndexedOptionForm('i8', ...)` - expects int32/uint32/int64

## Reproducing the Bug

```python
import awkward.forms as forms

# Case 1: BitMaskedForm
form1 = forms.BitMaskedForm('i8', forms.EmptyForm(), False, False)
form1.length_zero_array()  # TypeError: BitMaskedArray 'mask' must be an Index with dtype=uint8

# Case 2: IndexedForm  
form2 = forms.IndexedForm('i8', forms.EmptyForm())
form2.length_zero_array()  # TypeError: IndexedArray 'index' must be an Index with dtype in (int32, uint32, int64)

# Case 3: IndexedOptionForm
form3 = forms.IndexedOptionForm('i8', forms.EmptyForm())
form3.length_zero_array()  # TypeError: IndexedOptionArray 'index' must be an Index with dtype in (int32, uint32, int64)
```

## Why This Is A Bug

The Form classes define an API contract by accepting certain index types in their constructors. Users reasonably expect that forms constructed with valid parameters will work correctly with all Form methods. However, the underlying Array implementations have stricter requirements:

- BitMaskedArray/ByteMaskedArray require uint8 masks only
- IndexedArray/IndexedOptionArray require int32/uint32/int64 indices only

This violates the principle of least surprise and the API contract. Either:
1. The Form constructors should validate and reject unsupported index types
2. The Array implementations should support all index types the Forms accept

## Fix

The Forms should validate index types during construction to match what the Array implementations support:

```diff
--- a/awkward/forms/bitmaskedform.py
+++ b/awkward/forms/bitmaskedform.py
@@ -40,6 +40,9 @@ class BitMaskedForm(BitMaskedMeta[Form], Form):
         if not isinstance(mask, str):
             raise TypeError(
                 f"{type(self).__name__} 'mask' must be of type str, not {mask!r}"
             )
+        if mask not in ["u8"]:
+            raise ValueError(
+                f"{type(self).__name__} 'mask' must be 'u8', not {mask!r}"
+            )

--- a/awkward/forms/indexedform.py
+++ b/awkward/forms/indexedform.py
@@ -34,6 +34,9 @@ class IndexedForm(IndexedMeta[Form], Form):
         if not isinstance(index, str):
             raise TypeError(
                 f"{type(self).__name__} 'index' must be of type str, not {index!r}"
             )
+        if index not in ["i32", "u32", "i64"]:
+            raise ValueError(
+                f"{type(self).__name__} 'index' must be one of 'i32', 'u32', 'i64', not {index!r}"
+            )
```