# Bug Report: srsly.ruamel_yaml Round-trip Failure with U+0085 Character

**Target**: `srsly.ruamel_yaml` (specifically `yaml_dumps` and `yaml_loads`)
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The YAML serialization/deserialization functions incorrectly handle the Unicode character U+0085 (Next Line) in dictionary keys, replacing it with a space during round-trip operations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from srsly._yaml_api import yaml_dumps, yaml_loads

@given(st.dictionaries(st.text(min_size=1), st.none(), max_size=10))
def test_round_trip_property(data):
    serialized = yaml_dumps(data)
    deserialized = yaml_loads(serialized)
    assert data == deserialized
```

**Failing input**: `{'0\x85': None}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')
from srsly._yaml_api import yaml_dumps, yaml_loads

data = {'0\x85': None}
serialized = yaml_dumps(data)
deserialized = yaml_loads(serialized)

print(f"Original: {repr(data)}")
print(f"After round-trip: {repr(deserialized)}")
print(f"Keys match: {list(data.keys())[0] == list(deserialized.keys())[0]}")
```

## Why This Is A Bug

The YAML specification allows U+0085 in strings, but the implementation incorrectly treats it as a line break character during flow scalar scanning and replaces it with a space. This violates the round-trip property that `yaml_loads(yaml_dumps(x))` should equal `x` for valid YAML data.

## Fix

The issue occurs in the scanner and emitter modules where U+0085 is treated as a line break. The fix would involve properly escaping or preserving this character in quoted strings:

```diff
--- a/srsly/ruamel_yaml/scanner.py
+++ b/srsly/ruamel_yaml/scanner.py
@@ -1503,7 +1503,10 @@ class Scanner:
         elif ch in "\r\n\x85\u2028\u2029":
             line_break = self.scan_line_break()
             breaks = self.scan_flow_scalar_breaks(double, start_mark)
-            if line_break != "\n":
+            # Preserve NEL character in quoted strings
+            if ch == '\x85' and (single or double):
+                chunks.append(ch)
+            elif line_break != "\n":
                 chunks.append(line_break)
             elif not breaks:
                 chunks.append(" ")
```

Note: A complete fix would require careful handling in both the emitter and scanner to ensure U+0085 is properly escaped when necessary while maintaining compatibility with the YAML specification.