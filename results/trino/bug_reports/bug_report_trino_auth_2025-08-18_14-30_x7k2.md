# Bug Report: trino.auth._OAuth2TokenBearer._parse_authenticate_header Multiple Parsing Issues

**Target**: `trino.auth._OAuth2TokenBearer._parse_authenticate_header`
**Severity**: Medium
**Bug Type**: Crash, Logic
**Date**: 2025-08-18

## Summary

The `_parse_authenticate_header` method has multiple parsing issues: it crashes on empty values with IndexError, incorrectly parses values containing commas, and improperly handles keys with spaces.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import trino.auth as auth

@given(
    components=st.lists(
        st.tuples(
            st.text(alphabet=st.characters(blacklist_characters='=,"\n\r'), min_size=1, max_size=20),
            st.text(min_size=0, max_size=50).filter(lambda x: '\n' not in x and '\r' not in x)
        ),
        min_size=1,
        max_size=10
    )
)
def test_parse_authenticate_header_lowercases_keys(components):
    header_parts = []
    for key, value in components:
        if ',' in value or ' ' in value:
            header_parts.append(f'{key}="{value}"')
        else:
            header_parts.append(f'{key}={value}')
    
    header = ', '.join(header_parts)
    result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
    
    for key in result.keys():
        assert key == key.lower()
```

**Failing input**: `components=[('0', '')]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')
import trino.auth as auth

# Bug 1: IndexError on empty values
try:
    header = "key="
    result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
except IndexError as e:
    print(f"Bug 1 - IndexError on empty value: {e}")

# Bug 2: Incorrect parsing of values with commas
header = "key=value,with,comma"
result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
print(f"Bug 2 - Expected 'value,with,comma', got: '{result.get('key')}'")

# Bug 3: Keys with spaces not handled correctly  
header = " key with spaces =value"
result = auth._OAuth2TokenBearer._parse_authenticate_header(header)
print(f"Bug 3 - Key with spaces becomes: {list(result.keys())}")
```

## Why This Is A Bug

The method is used to parse WWW-Authenticate headers in OAuth2 authentication flow. These bugs violate expected behavior:

1. **IndexError**: Empty values in headers (e.g., `key=`) should be handled gracefully, not crash
2. **Comma parsing**: Values containing commas should be preserved intact when not quoted
3. **Key trimming**: Leading/trailing spaces in keys should be handled consistently

These issues could cause authentication failures or crashes when the server sends authentication headers with edge-case formatting.

## Fix

```diff
--- a/trino/auth.py
+++ b/trino/auth.py
@@ -571,11 +571,15 @@ class _OAuth2TokenBearer(AuthBase):
         for component in components:
             component = component.strip()
             if "=" in component:
                 key, value = component.split("=", 1)
-                if value[0] == '"' and value[-1] == '"':
+                key = key.strip().lower()
+                value = value.strip()
+                
+                if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                     value = value[1:-1]
-                auth_info_headers[key.lower()] = value
+                
+                auth_info_headers[key] = value
         return auth_info_headers
```