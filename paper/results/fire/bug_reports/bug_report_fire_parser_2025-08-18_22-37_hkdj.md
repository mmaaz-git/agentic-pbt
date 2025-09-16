# Bug Report: fire.parser Unicode Character Corruption

**Target**: `fire.parser.DefaultParseValue`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

DefaultParseValue silently corrupts the micro sign (µ U+00B5) by converting it to Greek mu (μ U+03BC), violating the documented behavior that simple strings pass through unchanged.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fire.parser as parser

@given(st.text(min_size=1).filter(lambda x: not any(c in x for c in ['"', "'", '\\', '(', ')', '[', ']', '{', '}', ',', ':', '#'])))
def test_default_parse_value_bareword_as_string(s):
    """Test that bare words without special chars are treated as strings."""
    # Skip Python keywords and numbers
    if s in ['True', 'False', 'None']:
        return
    try:
        float(s)
        return
    except ValueError:
        pass
    
    result = parser.DefaultParseValue(s)
    
    # Property: Bare words should be returned as strings unchanged
    assert result == s
```

**Failing input**: `'µ'`

## Reproducing the Bug

```python
import fire.parser as parser

micro_sign = 'µ'  # U+00B5 MICRO SIGN
result = parser.DefaultParseValue(micro_sign)

print(f"Input: '{micro_sign}' (U+{ord(micro_sign):04X})")
print(f"Result: '{result}' (U+{ord(result):04X})")
print(f"Are they equal? {micro_sign == result}")

# Output:
# Input: 'µ' (U+00B5)
# Result: 'μ' (U+03BC)
# Are they equal? False
```

## Why This Is A Bug

This violates the expected behavior that simple string arguments pass through unchanged. The micro sign is commonly used in scientific applications (µm, µs, µA) and file names. When users pass 'data_10µm.csv' as an argument, the function receives 'data_10μm.csv', potentially causing FileNotFoundError or data corruption. The root cause is Python's NFKC normalization of identifiers in ast.parse(), which converts U+00B5 to U+03BC.

## Fix

```diff
--- a/fire/parser.py
+++ b/fire/parser.py
@@ -119,7 +119,7 @@ def _LiteralEval(value):
 def _Replacement(node):
   """Returns a node to use in place of the supplied node in the AST.
 
   Args:
     node: A node of type Name. Could be a variable, or builtin constant.
   Returns:
     A node to use in place of the supplied Node. Either the same node, or a
     String node whose value matches the Name node's id.
   """
   value = node.id
   # These are the only builtin constants supported by literal_eval.
   if value in ('True', 'False', 'None'):
     return node
+  # Preserve the original representation if Unicode normalization changed it
+  # Note: This would require passing the original source to detect changes
   return _StrNode(value)
```

A complete fix would require passing the original source string through _LiteralEval to _Replacement to detect when ast.parse() has normalized Unicode characters, then preserving the original character instead of using the normalized version.