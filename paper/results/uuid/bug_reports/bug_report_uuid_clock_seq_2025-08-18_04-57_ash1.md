# Bug Report: uuid Module clock_seq Property Returns Incorrect Values for Non-RFC 4122 UUIDs

**Target**: `uuid.UUID.clock_seq`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `UUID.clock_seq` property incorrectly applies RFC 4122 bit masking to all UUID variants, causing it to return wrong values for non-RFC 4122 UUIDs (NCS, Microsoft, and Future variants).

## Property-Based Test

```python
from hypothesis import given, strategies as st
import uuid

valid_fields = st.tuples(
    st.integers(min_value=0, max_value=(1 << 32) - 1),
    st.integers(min_value=0, max_value=(1 << 16) - 1),
    st.integers(min_value=0, max_value=(1 << 16) - 1),
    st.integers(min_value=0, max_value=(1 << 8) - 1),
    st.integers(min_value=0, max_value=(1 << 8) - 1),
    st.integers(min_value=0, max_value=(1 << 48) - 1),
)

@given(valid_fields)
def test_field_accessors(fields):
    u = uuid.UUID(fields=fields)
    time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node = fields
    
    clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low
    assert u.clock_seq == clock_seq
```

**Failing input**: `(0, 0, 0, 64, 0, 0)`

## Reproducing the Bug

```python
import uuid

fields = (0, 0, 0, 0x40, 0x00, 0)
u = uuid.UUID(fields=fields)

expected_clock_seq = (0x40 << 8) | 0x00  
actual_clock_seq = u.clock_seq

print(f"UUID variant: {u.variant}")
print(f"Expected clock_seq: {expected_clock_seq}")
print(f"Actual clock_seq: {actual_clock_seq}")

assert expected_clock_seq == actual_clock_seq
```

## Why This Is A Bug

The `clock_seq` property in `/home/linuxbrew/.linuxbrew/Cellar/python@3.13/3.13.6/lib/python3.13/uuid.py:329` unconditionally masks `clock_seq_hi_variant` with `0x3f`, which is only correct for RFC 4122 UUIDs where the upper 2 bits are variant indicators. For non-RFC 4122 UUIDs (NCS, Microsoft, Future variants), these bits are part of the clock sequence value itself, not variant indicators. This causes the property to return incorrect values, violating the expected relationship: `clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low`.

## Fix

```diff
--- a/uuid.py
+++ b/uuid.py
@@ -327,8 +327,12 @@ class UUID:
 
     @property
     def clock_seq(self):
-        return (((self.clock_seq_hi_variant & 0x3f) << 8) |
-                self.clock_seq_low)
+        if self.variant == RFC_4122:
+            # For RFC 4122, upper 2 bits are variant, only use lower 6 bits
+            return (((self.clock_seq_hi_variant & 0x3f) << 8) |
+                    self.clock_seq_low)
+        else:
+            # For other variants, use all 8 bits
+            return ((self.clock_seq_hi_variant << 8) | self.clock_seq_low)
 
     @property
     def node(self):
```