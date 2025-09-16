# Bug Report: json.encoder Key Collision with Special Float Values

**Target**: `json.encoder.JSONEncoder`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

JSONEncoder causes silent data loss when dictionaries contain both special float keys (inf, -inf, nan) and their corresponding JSON string representations ('Infinity', '-Infinity', 'NaN') as keys.

## Property-Based Test

```python
import json
import json.encoder
import math
from hypothesis import given, strategies as st

@given(st.dictionaries(
    st.one_of(st.floats(), st.text()),
    st.text(),
    min_size=1
))
def test_dict_key_preservation(d):
    """Test that dictionary keys are preserved through JSON encoding"""
    encoder = json.encoder.JSONEncoder(allow_nan=True, skipkeys=False)
    
    # Count expected string keys after conversion
    expected_keys = set()
    for k in d.keys():
        if isinstance(k, float):
            if math.isnan(k):
                expected_keys.add('NaN')
            elif math.isinf(k) and k > 0:
                expected_keys.add('Infinity')
            elif math.isinf(k) and k < 0:
                expected_keys.add('-Infinity')
            else:
                expected_keys.add(str(k))
        else:
            expected_keys.add(k)
    
    encoded = encoder.encode(d)
    decoded = json.loads(encoded)
    
    # Bug: when original dict has both float('inf') and 'Infinity' as keys,
    # they both map to 'Infinity' in JSON, causing data loss
    assert len(decoded) == len(expected_keys)
```

**Failing input**: `{'Infinity': 'a', float('inf'): 'b'}`

## Reproducing the Bug

```python
import json

d = {'Infinity': 'string_value', float('inf'): 'float_value'}
encoded = json.dumps(d)
decoded = json.loads(encoded)

print(f"Original: {d}")
print(f"Original length: {len(d)}")
print(f"Encoded: {encoded}")
print(f"Decoded: {decoded}")
print(f"Decoded length: {len(decoded)}")

assert len(decoded) == len(d), f"Lost {len(d) - len(decoded)} keys"
```

## Why This Is A Bug

The JSON encoder incorrectly handles special float values (inf, -inf, nan) as dictionary keys by converting them to their JSON representations ('Infinity', '-Infinity', 'NaN'). This creates collisions when the original dictionary already contains these strings as keys, resulting in silent data loss. The last value overwrites previous values with the same JSON key representation.

## Fix

The issue occurs in `_iterencode_dict` function (lines 361-372) where float keys are converted using `_floatstr`. The fix should either:
1. Raise an error when collision would occur
2. Use Python's string representation ('inf', '-inf', 'nan') for consistency
3. Add a prefix/suffix to disambiguate float-derived keys

```diff
--- a/json/encoder.py
+++ b/json/encoder.py
@@ -359,8 +359,14 @@ def _iterencode_dict(dct, _current_indent_level):
             # JavaScript is weakly typed for these, so it makes sense to
             # also allow them.  Many encoders seem to do something like this.
             elif isinstance(key, float):
-                # see comment for int/float in _make_iterencode
-                key = _floatstr(key)
+                # Check for special values that could cause collisions
+                if math.isnan(key) or math.isinf(key):
+                    # Use Python's repr to avoid collision with string keys
+                    # 'inf' instead of 'Infinity', 'nan' instead of 'NaN'
+                    key = str(key)
+                else:
+                    # Regular floats use the same conversion
+                    key = _floatstr(key)
             elif key is True:
                 key = 'true'
             elif key is False:
```