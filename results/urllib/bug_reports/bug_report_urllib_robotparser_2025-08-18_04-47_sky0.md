# Bug Report: urllib.robotparser Double URL Encoding in RuleLine

**Target**: `urllib.robotparser.RuleLine`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The RuleLine class in urllib.robotparser double-encodes URL paths when a RuleLine is created with an already-encoded path, causing incorrect path matching behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import urllib.robotparser

@given(st.text(min_size=0, max_size=100).map(lambda s: '/' + s.strip('/')))
def test_ruleline_path_normalization_idempotent(path):
    rule1 = urllib.robotparser.RuleLine(path, True)
    rule2 = urllib.robotparser.RuleLine(rule1.path, True)
    assert rule1.path == rule2.path
```

**Failing input**: `path='/:' `

## Reproducing the Bug

```python
import urllib.robotparser

rule1 = urllib.robotparser.RuleLine('/:', True)
print(f"First encoding: {rule1.path}")

rule2 = urllib.robotparser.RuleLine(rule1.path, True)
print(f"Second encoding: {rule2.path}")

print(f"Should be equal: {rule1.path == rule2.path}")
```

## Why This Is A Bug

URL encoding should be idempotent when the input is already properly encoded. The RuleLine constructor unconditionally encodes the path using `urllib.parse.quote()`, even if the path is already encoded. This breaks the invariant that creating a RuleLine from another RuleLine's path should produce an equivalent rule.

## Fix

```diff
--- a/urllib/robotparser.py
+++ b/urllib/robotparser.py
@@ -222,7 +222,11 @@ class RuleLine:
         if path == '' and not allowance:
             # an empty value means allow all
             allowance = True
         path = urllib.parse.urlunparse(urllib.parse.urlparse(path))
-        self.path = urllib.parse.quote(path)
+        # Only quote if not already quoted
+        try:
+            self.path = path if path == urllib.parse.unquote(path, errors='strict') else urllib.parse.quote(path)
+        except:
+            self.path = urllib.parse.quote(path)
         self.allowance = allowance
```