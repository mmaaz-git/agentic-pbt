# Bug Report: troposphere Empty Property Name Causes Unhelpful Error

**Target**: `troposphere.AWSProperty`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

When an empty string is used as a property name in troposphere AWSProperty classes, it produces an AttributeError with an empty attribute name in the error message, making debugging difficult.

## Property-Based Test

```python
@given(
    key=st.one_of(st.none(), st.text()),
    value=st.one_of(st.none(), st.text()),
    extra_kwargs=st.dictionaries(
        st.text().filter(lambda x: x not in ["Key", "Value", "key", "value"]),
        st.text()
    )
)
def test_keyvalue_class_initialization(key, value, extra_kwargs):
    kwargs = extra_kwargs.copy()
    try:
        kv = emr_validators.KeyValueClass(key=key, value=value, **kwargs)
        if key is not None:
            assert kv.properties.get("Key") == key
        if value is not None:
            assert kv.properties.get("Value") == value
    except TypeError:
        pass
```

**Failing input**: `key=None, value=None, extra_kwargs={'': ''}`

## Reproducing the Bug

```python
from troposphere.validators import emr as emr_validators

kv = emr_validators.KeyValueClass(**{"": "value"})
```

## Why This Is A Bug

The error message "KeyValueClass object does not support attribute " (with no attribute name shown) is confusing and unhelpful for debugging. The code should either accept empty strings as valid property names or provide a clearer error message.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -311,6 +311,9 @@ class BaseAWSObject(dict):
             # validation. The properties of a CustomResource is not known.
             return self.properties.__setitem__(name, value)
     
+        if not name:
+            raise AttributeError(
+                "%s object does not support empty string as attribute name" % type_name
+            )
         raise AttributeError(
             "%s object does not support attribute %s" % (type_name, name)
         )
```