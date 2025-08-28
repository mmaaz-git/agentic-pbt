# Bug Report: fire.parser.DefaultParseValue Unicode Surrogate Pair Handling

**Target**: `fire.parser.DefaultParseValue`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

DefaultParseValue incorrectly handles Unicode characters outside the Basic Multilingual Plane (BMP) when parsing JSON strings, keeping surrogate pairs as literal strings instead of decoding them to the original characters.

## Property-Based Test

```python
import json
import fire.parser as parser
from hypothesis import given, strategies as st

@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=3))
def test_defaultparsevalue_roundtrip(value):
    str_value = json.dumps(value)
    parsed = parser.DefaultParseValue(str_value)
    assert parsed == value
```

**Failing input**: `{'𐀀': 0}`

## Reproducing the Bug

```python
import json
import fire.parser as parser

test_dict = {'𐀀': 0}
json_str = json.dumps(test_dict)
parsed = parser.DefaultParseValue(json_str)

print(f"Original: {test_dict}")
print(f"Parsed:   {parsed}")
print(f"Equal: {test_dict == parsed}")
```

## Why This Is A Bug

DefaultParseValue uses ast.literal_eval internally, which doesn't properly decode JSON Unicode escape sequences for surrogate pairs. When a character like '𐀀' (U+10000) is JSON-encoded as "\ud800\udc00", the parser keeps it as the literal string '\ud800\udc00' instead of decoding it back to '𐀀'. This breaks the round-trip property for valid JSON data containing Unicode characters outside the BMP.

## Fix

The fix would require detecting JSON-like strings and using json.loads instead of ast.literal_eval, or post-processing the result to decode surrogate pairs:

```diff
def DefaultParseValue(value):
    """Parse a value using ast.literal_eval or json.loads as appropriate."""
    if value == 'None':
        return None
    
    try:
+       # Try JSON first for better Unicode handling
+       if value.startswith(('{', '[')):
+           import json
+           return json.loads(value)
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        # Treat as string if not a valid literal
        return value
```