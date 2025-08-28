# Bug Report: awkward._connect.cling RecordArrayGenerator Fields Type Inconsistency

**Target**: `awkward._connect.cling.RecordArrayGenerator`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

RecordArrayGenerator.__init__ converts list fields to tuple, causing type inconsistency between the original RecordForm and the generated RecordArrayGenerator.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import awkward.forms as forms
from awkward._connect import cling

@st.composite
def record_forms(draw):
    n_fields = draw(st.integers(min_value=1, max_value=5))
    fields = [f"field_{i}" for i in range(n_fields)]
    contents = [forms.NumpyForm("float64") for _ in range(n_fields)]
    return forms.RecordForm(contents, fields)

@given(form=record_forms())
def test_record_fields_preservation(form):
    gen = cling.togenerator(form, flatlist_as_rvec=False)
    assert gen.fields == form.fields  # This fails!
    assert type(gen.fields) == type(form.fields)  # This also fails!
```

**Failing input**: `RecordForm([NumpyForm('float64')], ['field_0'])`

## Reproducing the Bug

```python
import awkward.forms as forms
from awkward._connect import cling

# Create a RecordForm with list fields
contents = [forms.NumpyForm('float64')]
list_fields = ['field_0']
record_form = forms.RecordForm(contents, list_fields)

# Convert to generator
gen = cling.togenerator(record_form, flatlist_as_rvec=False)

# Check types and values
print(f"RecordForm.fields: {record_form.fields}, type: {type(record_form.fields)}")
print(f"Generator.fields: {gen.fields}, type: {type(gen.fields)}")
print(f"Are they equal? {gen.fields == record_form.fields}")
```

## Why This Is A Bug

The RecordArrayGenerator constructor converts list fields to tuple (line 1412 in cling.py), breaking type consistency. Forms expect fields to maintain their original type, but the conversion changes lists to tuples, causing equality comparisons to fail and potentially breaking downstream code that expects consistent types.

## Fix

```diff
--- a/awkward/_connect/cling.py
+++ b/awkward/_connect/cling.py
@@ -1409,7 +1409,7 @@ class RecordArrayGenerator(Generator, ak._lookup.RecordLookup):
 
     def __init__(self, contents, fields, parameters, flatlist_as_rvec):
         self.contenttypes = tuple(contents)
-        self.fields = None if fields is None else tuple(fields)
+        self.fields = fields  # Preserve original type (list or tuple)
         self.parameters = parameters
         self.flatlist_as_rvec = flatlist_as_rvec