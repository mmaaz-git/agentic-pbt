# Bug Report: quickbooks.mixins ToJsonMixin.json_filter Decimal Handling

**Target**: `quickbooks.mixins.ToJsonMixin.json_filter`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `json_filter` method in `ToJsonMixin` fails to convert `Decimal` objects to strings within the dictionary comprehension, only converting them at the top level of the lambda function.

## Property-Based Test

```python
@given(
    st.dictionaries(
        st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20),
        st.one_of(
            st.none(),
            st.decimals(allow_nan=False, allow_infinity=False),
            st.integers(),
            st.text()
        ),
        min_size=0,
        max_size=10
    )
)
def test_json_filter_with_decimals(attributes):
    """Test json_filter properly handles Decimal objects"""
    
    class TestObject(ToJsonMixin):
        def __init__(self):
            pass
    
    obj = TestObject()
    
    for key, value in attributes.items():
        setattr(obj, key, value)
    
    filter_func = obj.json_filter()
    filtered_dict = filter_func(obj)
    
    for key, value in attributes.items():
        if not key.startswith('_') and value is not None:
            if isinstance(value, decimal.Decimal):
                assert filtered_dict[key] == str(value)
```

**Failing input**: `attributes={'0': Decimal('0')}`

## Reproducing the Bug

```python
import decimal
from quickbooks.mixins import ToJsonMixin

class TestObject(ToJsonMixin):
    def __init__(self):
        pass

obj = TestObject()
obj.value = decimal.Decimal('0')

filter_func = obj.json_filter()
filtered_dict = filter_func(obj)

print(f"Type of filtered value: {type(filtered_dict['value'])}")
print(f"Expected: str, Got: {type(filtered_dict['value']).__name__}")

assert isinstance(filtered_dict['value'], str), "Decimal not converted to string"
```

## Why This Is A Bug

The `json_filter` method's lambda function checks if the top-level `obj` is a Decimal and converts it to string, but when processing object attributes in the dict comprehension, it returns raw values without checking if they are Decimals. This violates the method's apparent contract of handling Decimal conversion, as evidenced by the outer `isinstance(obj, decimal.Decimal)` check. The inconsistency means filtered dictionaries containing Decimal values cannot be directly JSON-serialized without the DecimalEncoder, which could cause unexpected failures in code that relies on json_filter's output.

## Fix

```diff
--- a/quickbooks/mixins.py
+++ b/quickbooks/mixins.py
@@ -21,8 +21,11 @@ class ToJsonMixin(object):
         filter out properties that have names starting with _
         or properties that have a value of None
         """
-        return lambda obj: str(obj) if isinstance(obj, decimal.Decimal) else dict((k, v) for k, v in obj.__dict__.items()
-                                if not k.startswith('_') and getattr(obj, k) is not None)
+        return lambda obj: str(obj) if isinstance(obj, decimal.Decimal) else dict(
+            (k, str(v) if isinstance(v, decimal.Decimal) else v) 
+            for k, v in obj.__dict__.items()
+            if not k.startswith('_') and getattr(obj, k) is not None
+        )
 
 
 class FromJsonMixin(object):
```