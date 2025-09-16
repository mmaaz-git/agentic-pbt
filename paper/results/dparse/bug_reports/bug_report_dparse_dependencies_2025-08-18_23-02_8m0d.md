# Bug Report: dparse.dependencies Incorrect full_name Formatting When extras Is String

**Target**: `dparse.dependencies.Dependency`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `Dependency.full_name` property incorrectly formats package names when `extras` is passed as a string instead of a list, treating the string as an iterable of characters and joining them with commas.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import dparse.dependencies as deps
from packaging.specifiers import SpecifierSet

@given(st.text(min_size=1, max_size=20))
def test_extras_string_hypothesis(extras_str):
    """Test various strings as extras value"""
    dep = deps.Dependency(name="package", specs=SpecifierSet(), line="test", extras=extras_str)
    
    # String will be iterated character by character
    full_name = dep.full_name
    expected = f"package[{','.join(extras_str)}]"
    assert full_name == expected
```

**Failing input**: `extras_str="security"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

import dparse.dependencies as deps
from packaging.specifiers import SpecifierSet

dep = deps.Dependency(
    name="requests",
    specs=SpecifierSet(">=2.0.0"),
    line="requests[security]>=2.0.0",
    extras="security"
)

print(f"Expected: requests[security]")
print(f"Actual:   {dep.full_name}")

assert dep.full_name == "requests[s,e,c,u,r,i,t,y]"
```

## Why This Is A Bug

The `extras` parameter is documented and expected to be a list of strings representing package extras (like `["security", "socks"]`). However, if a user mistakenly passes a single string instead of a list, the `full_name` property treats the string as an iterable of characters and joins them with commas, producing malformed output like `package[s,e,c,u,r,i,t,y]` instead of the intended `package[security]`.

This violates the expected behavior because:
1. The resulting format is invalid according to PEP 508 package naming conventions
2. It silently produces incorrect output instead of failing fast or handling the common mistake gracefully
3. The serialization round-trip preserves this incorrect data, propagating the error

## Fix

```diff
--- a/dparse/dependencies.py
+++ b/dparse/dependencies.py
@@ -82,6 +82,10 @@ class Dependency:
 
         :return:
         """
+        # Handle common mistake of passing string instead of list for extras
+        if isinstance(self.extras, str):
+            return "{}[{}]".format(self.name, self.extras)
+        
         if self.extras:
             return "{}[{}]".format(self.name, ",".join(self.extras))
         return self.name
```