# Bug Report: sentinels Mutable Name Breaks Singleton Contract

**Target**: `sentinels.Sentinel`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `_name` attribute of Sentinel objects can be modified after creation, breaking the singleton contract and causing repr inconsistency.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sentinels import Sentinel

@given(st.text(min_size=1), st.text(min_size=1))
def test_name_immutability_preserves_singleton_contract(original_name, new_name):
    """Sentinel names should be immutable to preserve singleton semantics."""
    s1 = Sentinel(original_name)
    
    # Attempt to modify name
    s1._name = new_name
    
    # Get sentinel with original name again
    s2 = Sentinel(original_name)
    
    # These should be the same object
    assert s2 is s1
    
    # The repr should still show the original name
    assert repr(s2) == f"<{original_name}>"  # FAILS - shows <new_name>
```

**Failing input**: `original_name="foo", new_name="bar"`

## Reproducing the Bug

```python
from sentinels import Sentinel

# Create a sentinel named "foo"
sentinel = Sentinel("foo")
print(f"Created: {repr(sentinel)}")  # Output: <foo>

# Modify the internal name
sentinel._name = "bar"
print(f"After modification: {repr(sentinel)}")  # Output: <bar>

# Request "foo" sentinel again
same_sentinel = Sentinel("foo")
print(f"Sentinel('foo') returns: {repr(same_sentinel)}")  # Output: <bar>

# Bug: Sentinel("foo") returns object claiming to be <bar>
assert same_sentinel is sentinel  # True - same object
assert repr(same_sentinel) == "<foo>"  # FAILS - it's "<bar>"
```

## Why This Is A Bug

This violates the singleton pattern's contract. When calling `Sentinel("foo")`, users expect an object that consistently represents itself as `<foo>`. The ability to mutate `_name` breaks this guarantee, leading to confusing behavior where `Sentinel("foo")` returns an object with `repr() == "<bar>"`.

## Fix

```diff
--- a/sentinels/__init__.py
+++ b/sentinels/__init__.py
@@ -10,9 +10,14 @@
 class Sentinel(object):
     _existing_instances = {}
 
     def __init__(self, name):
         super(Sentinel, self).__init__()
-        self._name = name
+        self.__name = name  # Use name mangling for protection
         self._existing_instances[self._name] = self
+    
+    @property
+    def _name(self):
+        return self.__name
 
     def __repr__(self):
         return f"<{self._name}>"
```