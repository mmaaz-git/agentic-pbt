# Bug Report: pyatlan.utils.to_camel_case Idempotence Violation

**Target**: `pyatlan.utils.to_camel_case`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `to_camel_case` function is not idempotent. Applying it twice produces different results than applying it once, violating the expected mathematical property that f(f(x)) = f(x) for a case conversion function.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyatlan.utils import to_camel_case

@given(st.text(min_size=1, max_size=100))
def test_to_camel_case_idempotence(s):
    """Applying to_camel_case twice should be the same as applying once."""
    once = to_camel_case(s)
    twice = to_camel_case(once)
    assert once == twice, f"Not idempotent: {s} -> {once} -> {twice}"
```

**Failing input**: `'A_A'`

## Reproducing the Bug

```python
from pyatlan.utils import to_camel_case

test_input = 'A_A'
once = to_camel_case(test_input)
twice = to_camel_case(once)

print(f"Input: '{test_input}'")
print(f"First application: '{once}'")
print(f"Second application: '{twice}'")
print(f"Idempotent: {once == twice}")
```

Output:
```
Input: 'A_A'
First application: 'aA'
Second application: 'aa'
Idempotent: False
```

## Why This Is A Bug

The function is intended to convert strings to camelCase format. Once a string is in camelCase, applying the function again should not change it. However, the current implementation uses Python's `title()` method which lowercases all characters except the first in each word. When applied to already camelCased text like 'aA', it incorrectly converts it to 'aa'.

This violates the idempotence property that users would reasonably expect from a case conversion function. It means that repeatedly applying the function in a pipeline or when processing data multiple times could lead to unexpected data corruption.

## Fix

```diff
--- a/pyatlan/utils.py
+++ b/pyatlan/utils.py
@@ -35,7 +35,12 @@
 
 def to_camel_case(s: str) -> str:
-    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
-    return "".join([s[0].lower(), s[1:]])
+    # Check if already in camelCase to ensure idempotence
+    if not re.search(r"[_\-\s]", s) and s and s[0].islower():
+        return s
+    # Convert to camelCase
+    words = re.sub(r"[_\-\s]+", " ", s).split()
+    camel = "".join(word.capitalize() for word in words)
+    return camel[0].lower() + camel[1:] if camel else ""
```