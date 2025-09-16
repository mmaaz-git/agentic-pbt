# Bug Report: azure.core.utils.parse_connection_string Strips Leading Whitespace from Keys

**Target**: `azure.core.utils.parse_connection_string`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `parse_connection_string` function incorrectly strips leading whitespace from keys even when `case_sensitive_keys=True`, violating the expectation that keys should be preserved exactly.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from azure.core.utils import parse_connection_string

connection_key = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters='=;'),
    min_size=1,
    max_size=50
).filter(lambda s: s.strip() != '')

connection_value = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters=';'),
    min_size=1,
    max_size=100
).filter(lambda s: s.strip() != '' and '=' not in s.split('=', 1)[0])

@given(st.dictionaries(connection_key, connection_value, min_size=1, max_size=10))
def test_parse_connection_string_case_sensitive_preserves_case(conn_dict):
    conn_str = ';'.join(f'{k}={v}' for k, v in conn_dict.items())
    result = parse_connection_string(conn_str, case_sensitive_keys=True)
    assert set(result.keys()) == set(conn_dict.keys())
    for key, value in conn_dict.items():
        assert result[key] == value
```

**Failing input**: `{'\xa00': '0'}` (non-breaking space followed by '0')

## Reproducing the Bug

```python
from azure.core.utils import parse_connection_string

# Key with leading non-breaking space
key_with_nbsp = '\xa00'
conn_str = f"{key_with_nbsp}=value"

result = parse_connection_string(conn_str, case_sensitive_keys=True)

print(f"Original key: {repr(key_with_nbsp)}")
print(f"Parsed key: {repr(list(result.keys())[0])}")
print(f"Keys match: {list(result.keys())[0] == key_with_nbsp}")

# Also affects regular spaces
conn_str2 = " key=value"
result2 = parse_connection_string(conn_str2, case_sensitive_keys=True)
print(f"Original key with space: {repr(' key')}")
print(f"Parsed key: {repr(list(result2.keys())[0])}")
```

## Why This Is A Bug

When `case_sensitive_keys=True` is specified, the documentation states that "the original casing of the keys will be preserved". By extension, the entire key should be preserved as-is, including any leading whitespace. The current behavior strips leading whitespace, which modifies the key and violates the preservation guarantee.

This is especially problematic for:
1. Connection strings where whitespace in keys is significant
2. Systems that distinguish between keys with and without leading whitespace
3. Round-trip scenarios where the original key format must be maintained

## Fix

```diff
--- a/azure/core/utils/_connection_string_parser.py
+++ b/azure/core/utils/_connection_string_parser.py
@@ -14,7 +14,9 @@ def parse_connection_string(conn_str: str, case_sensitive_keys: bool = False) -
     """
 
-    cs_args = [s.split("=", 1) for s in conn_str.strip().rstrip(";").split(";")]
+    # Only strip the overall connection string, not individual keys/values
+    conn_str_trimmed = conn_str.strip().rstrip(";")
+    cs_args = [s.split("=", 1) for s in conn_str_trimmed.split(";")]
     if any(len(tup) != 2 or not all(tup) for tup in cs_args):
         raise ValueError("Connection string is either blank or malformed.")
     args_dict = dict(cs_args)
```