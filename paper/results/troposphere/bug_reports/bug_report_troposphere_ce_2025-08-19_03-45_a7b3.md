# Bug Report: troposphere.ce Hash/Equality Contract Violation

**Target**: `troposphere.ce`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

AWSProperty subclasses in troposphere.ce (ResourceTag, Subscriber) violate Python's hash/equality contract, causing identical objects to have different hashes when used in sets or as dictionary keys.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.ce as ce

@given(key=st.text(min_size=1), value=st.text(min_size=1))
def test_hash_equality_contract(key, value):
    tag1 = ce.ResourceTag(Key=key, Value=value)
    tag2 = ce.ResourceTag(Key=key, Value=value)
    
    # Python contract: if a == b, then hash(a) == hash(b)
    if tag1 == tag2:
        assert hash(tag1) == hash(tag2), "Equal objects must have equal hashes"
    
    # Sets should recognize identical objects
    tag_set = {tag1, tag2}
    assert len(tag_set) == 1, "Set should contain only one element for identical objects"
```

**Failing input**: Any valid Key/Value pair, e.g., `Key="TestKey", Value="TestValue"`

## Reproducing the Bug

```python
import troposphere.ce as ce

# Create two identical ResourceTag objects
tag1 = ce.ResourceTag(Key="TestKey", Value="TestValue")
tag2 = ce.ResourceTag(Key="TestKey", Value="TestValue")

# Check equality and hash
print(f"tag1 == tag2: {tag1 == tag2}")  # True
print(f"hash(tag1) == hash(tag2): {hash(tag1) == hash(tag2)}")  # False!

# Demonstrate the problem
tag_set = {tag1, tag2}
print(f"Set size: {len(tag_set)}")  # 2 instead of 1!
```

## Why This Is A Bug

This violates Python's fundamental requirement that equal objects must have equal hashes. The bug occurs because:

1. `AWSProperty.__init__` accepts `title=None` as default
2. `BaseAWSObject.__eq__` compares objects including their titles
3. `BaseAWSObject.__hash__` generates different hashes for different object instances even when all properties are identical

This makes AWSProperty objects unreliable for use in sets, as dictionary keys, or any hash-based data structure.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -420,10 +420,12 @@ class BaseAWSObject:
 
     def __eq__(self, other: object) -> bool:
         if isinstance(other, self.__class__):
-            return self.title == other.title and self.to_json(
-                validation=False
-            ) == other.to_json(validation=False)
+            # For AWSProperty objects, only compare properties, not title
+            if isinstance(self, AWSProperty):
+                return self.to_dict(validation=False) == other.to_dict(validation=False)
+            else:
+                return self.title == other.title and self.to_dict(validation=False) == other.to_dict(validation=False)
         if isinstance(other, dict):
             return {"title": self.title, **self.to_dict()} == other
         return NotImplemented
 
@@ -431,7 +433,11 @@ class BaseAWSObject:
         return not self == other
 
     def __hash__(self) -> int:
-        return hash(json.dumps({"title": self.title, **self.to_dict()}, indent=0))
+        # For AWSProperty objects, exclude title from hash
+        if isinstance(self, AWSProperty):
+            return hash(json.dumps(self.to_dict(validation=False), indent=0, sort_keys=True))
+        else:
+            return hash(json.dumps({"title": self.title, **self.to_dict(validation=False)}, indent=0, sort_keys=True))
```