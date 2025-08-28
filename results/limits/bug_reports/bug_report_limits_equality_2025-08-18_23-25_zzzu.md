# Bug Report: RateLimitItem Equality-Hash Contract Violation

**Target**: `limits.limits.RateLimitItem`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

RateLimitItem's `__eq__` method ignores the namespace field, but `__hash__` includes it, violating Python's requirement that equal objects must have equal hashes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from limits.limits import RateLimitItemPerSecond

@given(
    st.sampled_from([RateLimitItemPerSecond]),
    st.integers(min_value=1, max_value=1000),
    st.integers(min_value=1, max_value=100)
)
def test_rate_limit_equality_and_hash(cls, amount, multiples):
    limit1 = cls(amount, multiples, "NS1")
    limit2 = cls(amount, multiples, "NS1")
    limit3 = cls(amount, multiples, "NS2")
    
    assert limit1 == limit2
    assert hash(limit1) == hash(limit2)
    
    assert limit1 != limit3
    assert hash(limit1) != hash(limit3)
```

**Failing input**: `cls=RateLimitItemPerSecond, amount=1, multiples=1`

## Reproducing the Bug

```python
from limits.limits import RateLimitItemPerSecond

limit1 = RateLimitItemPerSecond(1, 1, "NS1")
limit2 = RateLimitItemPerSecond(1, 1, "NS2")

print(limit1 == limit2)  # True
print(hash(limit1) == hash(limit2))  # False
```

## Why This Is A Bug

Python requires that if `a == b` then `hash(a) == hash(b)`. The current implementation violates this contract because `__eq__` doesn't check namespace but `__hash__` includes it. This can cause incorrect behavior in sets and dictionaries, where two "equal" rate limits with different namespaces would be treated as distinct despite comparing as equal.

## Fix

```diff
--- a/limits/limits.py
+++ b/limits/limits.py
@@ -126,10 +126,11 @@ class RateLimitItem(metaclass=RateLimitItemMeta):
     def __eq__(self, other: object) -> bool:
         if isinstance(other, RateLimitItem):
             return (
                 self.amount == other.amount
                 and self.GRANULARITY == other.GRANULARITY
                 and self.multiples == other.multiples
+                and self.namespace == other.namespace
             )
         return False
```