# Bug Report: Fire Parser Fails to Parse YAML-like Dicts with Python Keywords

**Target**: `fire.parser.DefaultParseValue`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Fire's YAML-like dict parsing fails when keys are Python keywords (e.g., 'as', 'if', 'for'), returning the input as a string instead of parsing it as a dictionary.

## Property-Based Test

```python
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        st.one_of(st.integers(), st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))),
        min_size=1,
        max_size=5
    )
)
def test_yaml_like_dict_parsing(d):
    """Test that Fire can parse YAML-like dict syntax {a: b}."""
    items = []
    for key, value in d.items():
        if isinstance(value, str):
            items.append(f"{key}: {value}")
        else:
            items.append(f"{key}: {value}")
    yaml_like = "{" + ", ".join(items) + "}"
    
    result = parser.DefaultParseValue(yaml_like)
    
    assert isinstance(result, dict)
    assert set(result.keys()) == set(d.keys())
```

**Failing input**: `d={'as': 0}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import parser

# Works for non-keywords
result1 = parser.DefaultParseValue('{foo: 1}')
print(f"{result1} == {{'foo': 1}}: {result1 == {'foo': 1}}")

# Fails for Python keywords
result2 = parser.DefaultParseValue('{as: 2}')
print(f"Type of result2: {type(result2)}")
print(f"Result2: {result2}")
print(f"Is dict: {isinstance(result2, dict)}")
```

## Why This Is A Bug

The docstring for `_LiteralEval` states: "This allows for the YAML-like syntax {a: b} to represent the dict {'a': 'b'}". However, when 'a' is a Python keyword, the parsing fails silently and returns the input string unchanged. This violates the documented contract and prevents users from using common words like 'as', 'if', 'for' as dictionary keys in CLI arguments.

## Fix

The issue occurs because Python keywords cannot be parsed as `ast.Name` nodes. The fix would be to handle keywords specially in the parser:

```diff
--- a/fire/parser.py
+++ b/fire/parser.py
@@ -17,6 +17,7 @@
 import argparse
 import ast
 import sys
+import keyword
 
 if sys.version_info[0:2] < (3, 8):
   _StrNode = ast.Str
@@ -97,7 +98,14 @@ def _LiteralEval(value):
     SyntaxError: If the value string has a syntax error.
   """
-  root = ast.parse(value, mode='eval')
+  # First, try parsing with keywords replaced
+  temp_value = value
+  for kw in keyword.kwlist:
+    # Replace keywords with placeholders
+    temp_value = temp_value.replace(f'{{{kw}:', f'{{"__{kw}__":')
+    temp_value = temp_value.replace(f', {kw}:', f', "__{kw}__":')
+  
+  root = ast.parse(temp_value, mode='eval')
   if isinstance(root.body, ast.BinOp):
     raise ValueError(value)
```

Note: A more robust fix would require deeper changes to handle keywords properly throughout the AST transformation process.