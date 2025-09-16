# Bug Report: DynamoDB Deserializer Crashes on Numbers Over 38 Digits

**Target**: `aws_lambda_powertools.shared.dynamodb_deserializer.TypeDeserializer._deserialize_n`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The DynamoDB deserializer raises a `decimal.Inexact` exception when attempting to deserialize numbers with more than 38 significant digits, despite having code that attempts to handle this case.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer

@given(st.text(alphabet="0123456789", min_size=39, max_size=100))
def test_dynamodb_number_deserializer_precision_loss(number_str):
    deserializer = TypeDeserializer()
    assume(not all(c == '0' for c in number_str))
    dynamodb_value = {"N": number_str}
    result = deserializer.deserialize(dynamodb_value)
    assert isinstance(result, Decimal)
```

**Failing input**: `'1000000000000000000000000000000000000010'`

## Reproducing the Bug

```python
from aws_lambda_powertools.shared.dynamodb_deserializer import TypeDeserializer

deserializer = TypeDeserializer()
number_str = '1000000000000000000000000000000000000010'
dynamodb_value = {"N": number_str}

result = deserializer.deserialize(dynamodb_value)
```

## Why This Is A Bug

The `_deserialize_n` method includes logic (lines 84-89) to handle numbers longer than 38 digits by trimming them. However, this trimming happens after `lstrip("0")`, and the DYNAMODB_CONTEXT has traps enabled for `Inexact` and `Rounded` exceptions. When `create_decimal()` is called with the trimmed value, it still raises an exception due to the precision limit.

## Fix

```diff
--- a/aws_lambda_powertools/shared/dynamodb_deserializer.py
+++ b/aws_lambda_powertools/shared/dynamodb_deserializer.py
@@ -77,6 +77,9 @@ class TypeDeserializer:
     def _deserialize_n(self, value: str) -> Decimal:
         # value is None or "."? It's zero
         # then return early
+        # Store original value for later use
+        original_value = value
+        
         value = value.lstrip("0")
         if not value or value == ".":
             return DYNAMODB_CONTEXT.create_decimal(0)
@@ -88,7 +91,12 @@ class TypeDeserializer:
             # Trim the value: remove trailing zeros if any, or just take the first 38 characters
             value = value[:-tail] if tail > 0 else value[:38]
 
-        return DYNAMODB_CONTEXT.create_decimal(value)
+        # Temporarily disable traps for Inexact and Rounded to handle large numbers gracefully
+        temp_context = DYNAMODB_CONTEXT.copy()
+        temp_context.traps[Inexact] = 0
+        temp_context.traps[Rounded] = 0
+        
+        return temp_context.create_decimal(value)
 
     def _deserialize_s(self, value: str) -> str:
         return value
```