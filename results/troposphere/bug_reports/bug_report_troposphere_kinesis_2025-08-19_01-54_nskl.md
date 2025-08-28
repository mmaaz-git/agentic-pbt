# Bug Report: troposphere.kinesis Incorrect Error Message in kinesis_stream_mode Validator

**Target**: `troposphere.validators.kinesis.kinesis_stream_mode`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `kinesis_stream_mode` validator function raises a ValueError with an incorrect error message that references "ContentType" instead of "StreamMode".

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators.kinesis import kinesis_stream_mode

@given(st.text().filter(lambda x: x not in ["ON_DEMAND", "PROVISIONED"]))
def test_kinesis_stream_mode_error_message(invalid_mode):
    """Test that kinesis_stream_mode error message mentions 'ContentType' incorrectly"""
    try:
        kinesis_stream_mode(invalid_mode)
        assert False, f"Expected ValueError for invalid mode: {invalid_mode}"
    except ValueError as e:
        error_msg = str(e)
        # The bug: error message says "ContentType" but should reference StreamMode
        assert "ContentType" in error_msg, f"Error message doesn't contain 'ContentType': {error_msg}"
```

**Failing input**: Any string that is not "ON_DEMAND" or "PROVISIONED", e.g., `"INVALID"`

## Reproducing the Bug

```python
from troposphere.validators.kinesis import kinesis_stream_mode

try:
    kinesis_stream_mode("INVALID")
except ValueError as e:
    print(f"Error message: {e}")
    print(f"Bug confirmed: 'ContentType' in error? {('ContentType' in str(e))}")
```

## Why This Is A Bug

The function validates StreamMode values for AWS Kinesis streams, but the error message incorrectly refers to "ContentType". This creates confusion for users who receive an error mentioning a completely unrelated property name when providing invalid StreamMode values.

## Fix

```diff
--- a/troposphere/validators/kinesis.py
+++ b/troposphere/validators/kinesis.py
@@ -13,7 +13,7 @@ def kinesis_stream_mode(mode):
     """
     valid_modes = ["ON_DEMAND", "PROVISIONED"]
     if mode not in valid_modes:
-        raise ValueError('ContentType must be one of: "%s"' % (", ".join(valid_modes)))
+        raise ValueError('StreamMode must be one of: "%s"' % (", ".join(valid_modes)))
     return mode
```