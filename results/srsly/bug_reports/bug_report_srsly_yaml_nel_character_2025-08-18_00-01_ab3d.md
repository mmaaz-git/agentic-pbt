# Bug Report: srsly YAML Doesn't Preserve NEL Control Character in Dictionary Keys

**Target**: `srsly.yaml_dumps` / `srsly.yaml_loads`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

YAML serialization/deserialization silently converts the NEL (Next Line, U+0085) control character to a space (U+0020) when used in dictionary keys, causing data corruption.

## Property-Based Test

```python
@given(json_data)
@settings(max_examples=200)
def test_yaml_round_trip(data):
    """Test that yaml_loads(yaml_dumps(x)) == x"""
    serialized = srsly.yaml_dumps(data)
    deserialized = srsly.yaml_loads(serialized)
    assert deserialized == data
```

**Failing input**: `{'\x85': None}`

## Reproducing the Bug

```python
import srsly

original_data = {'\x85': None}  # NEL character as dictionary key
yaml_str = srsly.yaml_dumps(original_data)
deserialized = srsly.yaml_loads(yaml_str)

print(f"Original: {repr(original_data)}")
print(f"Deserialized: {repr(deserialized)}")
print(f"Keys match: {original_data == deserialized}")
```

## Why This Is A Bug

The YAML round-trip property should preserve data exactly. When a dictionary has the NEL control character (U+0085) as a key, it gets silently converted to a space character (U+0020) during serialization/deserialization. This violates the fundamental expectation that `yaml_loads(yaml_dumps(x)) == x` for valid YAML data, causing silent data corruption.

## Fix

The issue appears to be in the underlying ruamel.yaml library's handling of control characters in string keys. The fix would require either:
1. Escaping control characters properly during serialization
2. Using quoted strings for keys containing control characters
3. Documenting this limitation if it's inherent to the YAML spec

A workaround could be to pre-process dictionary keys to escape problematic characters before serialization.