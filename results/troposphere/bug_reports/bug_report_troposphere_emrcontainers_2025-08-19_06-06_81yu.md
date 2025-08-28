# Bug Report: troposphere.emrcontainers Inconsistent Empty String Handling

**Target**: `troposphere.emrcontainers`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict` class method inconsistently converts empty string titles to `None`, while direct instantiation preserves empty strings, violating the expected consistency between these construction methods.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.emrcontainers as emr

@given(
    title=st.text(min_size=0, max_size=10),
    namespace=st.text(min_size=1, max_size=100)
)
def test_from_dict_consistent_with_direct_instantiation(title, namespace):
    """Property: from_dict and direct instantiation should handle titles consistently"""
    # Create via direct instantiation
    direct = emr.EksInfo(title=title, Namespace=namespace)
    
    # Create via from_dict
    from_dict = emr.EksInfo.from_dict(title, {'Namespace': namespace})
    
    # Both should have the same title value
    assert direct.title == from_dict.title, \
        f"Title mismatch: direct={repr(direct.title)}, from_dict={repr(from_dict.title)}"
```

**Failing input**: `title=""`, `namespace="test"`

## Reproducing the Bug

```python
import troposphere.emrcontainers as emr

# Create EksInfo with empty title via from_dict
eks_from_dict = emr.EksInfo.from_dict("", {"Namespace": "test"})
print(f"from_dict('') title: {repr(eks_from_dict.title)}")

# Create EksInfo with empty title via direct instantiation
eks_direct = emr.EksInfo(title="", Namespace="test")
print(f"direct instantiation title: {repr(eks_direct.title)}")

# Bug: These should be equal but they're not
assert eks_from_dict.title != eks_direct.title
print(f"BUG: from_dict converts empty string to None, direct keeps empty string")
```

## Why This Is A Bug

This violates the principle of least surprise and API consistency. Users expect `from_dict` to be equivalent to direct instantiation for the same inputs. The inconsistent handling of empty strings means:

1. Round-trip operations may not preserve the original title value
2. Code that relies on one construction method may behave differently when switched to the other
3. The API contract is unclear about how empty titles should be handled

## Fix

The issue likely occurs in the `from_dict` method's title handling. A potential fix would ensure empty strings are preserved:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -406,7 +406,7 @@ class BaseAWSObject:
     @classmethod
     def from_dict(cls, title, d):
-        return cls._from_dict(title, **d)
+        return cls._from_dict(title if title else None, **d)
```

Note: The actual fix location may vary, but the key is to ensure consistent handling of empty string titles between both construction methods.