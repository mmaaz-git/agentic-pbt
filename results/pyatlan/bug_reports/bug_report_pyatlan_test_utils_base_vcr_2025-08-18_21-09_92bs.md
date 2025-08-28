# Bug Report: VCRPrettyPrintJSONBody.deserialize AttributeError on Non-Dictionary JSON

**Target**: `pyatlan.test_utils.base_vcr.VCRPrettyPrintJSONBody.deserialize`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

VCRPrettyPrintJSONBody.deserialize crashes with AttributeError when given valid JSON that doesn't parse to a dictionary (e.g., numbers, strings, arrays, booleans, null).

## Property-Based Test

```python
@given(st.text())
def test_vcr_json_deserialize_safety(cassette_string):
    """Test VCRPrettyPrintJSONBody.deserialize handles edge cases safely"""
    # Should not crash on any input
    result = VCRPrettyPrintJSONBody.deserialize(cassette_string)
    assert isinstance(result, dict)
    
    # Valid JSON should parse correctly
    if cassette_string.strip():
        try:
            json.loads(cassette_string)
            # If it's valid JSON, result should have content
            assert result != {} or cassette_string.strip() == "{}"
        except json.JSONDecodeError:
            # Invalid JSON should return empty dict
            assert result == {}
```

**Failing input**: `'0'`

## Reproducing the Bug

```python
from pyatlan.test_utils.base_vcr import VCRPrettyPrintJSONBody

# Any valid JSON that isn't a dictionary causes the crash
result = VCRPrettyPrintJSONBody.deserialize('0')
# AttributeError: 'int' object has no attribute 'get'

# Other failing inputs:
VCRPrettyPrintJSONBody.deserialize('42')        # int
VCRPrettyPrintJSONBody.deserialize('true')      # bool
VCRPrettyPrintJSONBody.deserialize('null')      # None
VCRPrettyPrintJSONBody.deserialize('"string"')  # str
VCRPrettyPrintJSONBody.deserialize('[1,2,3]')   # list
```

## Why This Is A Bug

The deserialize method assumes json.loads() always returns a dictionary, but valid JSON can be primitives (numbers, strings, booleans, null) or arrays at the top level. When it tries to call `.get("interactions", [])` on a non-dictionary value, it crashes with AttributeError. This violates the principle that a deserializer should handle all valid JSON gracefully.

## Fix

```diff
@staticmethod
def deserialize(cassette_string: str) -> dict:
    """
    Deserializes a JSON string into a dictionary and converts
    parsed_json fields back to string fields.
    """
    # Safety check for cassette_string
    if not cassette_string:
        return {}

    try:
        cassette_dict = json.loads(cassette_string)
    except json.JSONDecodeError:
        return {}

+   # Ensure we have a dictionary - if not, return empty dict
+   if not isinstance(cassette_dict, dict):
+       return {}
+
    # Convert parsed_json back to string format
    interactions = cassette_dict.get("interactions", []) or []
```