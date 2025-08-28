# Bug Report: pydantic.type_adapter TypeAdapter Violates Round-Trip Property for Bytes

**Target**: `pydantic.type_adapter.TypeAdapter`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

TypeAdapter accepts arbitrary bytes via `validate_python()` but fails to serialize non-UTF-8 bytes with `dump_json()`, violating the round-trip property.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic import TypeAdapter

@given(st.binary(max_size=1000))
def test_bytes_round_trip(value):
    """Test round-trip for bytes type."""
    ta = TypeAdapter(bytes)
    
    # Test JSON round-trip - bytes are base64 encoded in JSON
    json_bytes = ta.dump_json(value)
    recovered_json = ta.validate_json(json_bytes)
    assert recovered_json == value
    assert isinstance(recovered_json, bytes)
```

**Failing input**: `b'\x80'`

## Reproducing the Bug

```python
from pydantic import TypeAdapter

ta = TypeAdapter(bytes)

# Non-UTF-8 bytes
non_utf8_bytes = b'\x80'

# TypeAdapter accepts these bytes
validated = ta.validate_python(non_utf8_bytes)
assert validated == non_utf8_bytes

# But cannot serialize them to JSON
json_output = ta.dump_json(validated)  # Raises PydanticSerializationError
```

## Why This Is A Bug

The round-trip property should hold: any value accepted by `validate_python()` should be serializable via `dump_json()` and recoverable via `validate_json()`. TypeAdapter violates this contract by accepting bytes values it cannot serialize, making it impossible to round-trip arbitrary byte sequences through JSON.

## Fix

The bytes type should either:
1. Use base64 encoding for JSON serialization (recommended), or
2. Only accept UTF-8 valid bytes in `validate_python()` if JSON serialization requires UTF-8

Suggested fix using base64 encoding:

```diff
# In the serialization logic for bytes type
- serialize_bytes_as_utf8_string(bytes_value)  
+ import base64
+ base64.b64encode(bytes_value).decode('ascii')

# In the validation logic for bytes from JSON
- parse_string_as_utf8_bytes(json_string)
+ import base64  
+ base64.b64decode(json_string)
```