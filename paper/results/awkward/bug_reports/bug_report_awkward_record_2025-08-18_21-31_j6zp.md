# Bug Report: awkward.record.Record to_packed() changes 'at' position

**Target**: `awkward.record.Record.to_packed()`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `to_packed()` method of `awkward.record.Record` unexpectedly changes the record's `at` position from its original value to 0 when the underlying array has more than one element.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import numpy as np
import awkward as ak

@st.composite
def record_strategy(draw):
    length = draw(st.integers(min_value=2, max_value=100))
    n_fields = draw(st.integers(min_value=1, max_value=5))
    
    contents = []
    for _ in range(n_fields):
        data = np.array(draw(st.lists(
            st.integers(min_value=-1000, max_value=1000),
            min_size=length, max_size=length
        )), dtype=np.int32)
        contents.append(ak.contents.NumpyArray(data))
    
    fields = None if draw(st.booleans()) else [f"f{i}" for i in range(n_fields)]
    array = ak.contents.RecordArray(contents, fields=fields)
    at = draw(st.integers(min_value=1, max_value=length-1))
    return ak.record.Record(array, at)

@given(record_strategy())
def test_to_packed_preserves_position(record):
    original_at = record.at
    packed = record.to_packed()
    assert packed.at == original_at, f"to_packed changed position from {original_at} to {packed.at}"
```

**Failing input**: Any Record with `at > 0` and `array.length > 1`

## Reproducing the Bug

```python
import numpy as np
import awkward as ak

# Create a RecordArray with 5 elements
array = ak.contents.RecordArray(
    [
        ak.contents.NumpyArray(np.array([10, 20, 30, 40, 50])),
        ak.contents.NumpyArray(np.array([100, 200, 300, 400, 500]))
    ],
    fields=None
)

# Create a Record at position 4
record = ak.record.Record(array, at=4)
print(f"Original position: {record.at}")

# Call to_packed
packed = record.to_packed()
print(f"Packed position: {packed.at}")

# Bug: packed.at is 0 instead of 4
assert packed.at == 0  # Should be 4
```

## Why This Is A Bug

The `to_packed()` method is expected to create a packed version of the record while preserving its logical properties, including its position within the array. Changing the `at` position breaks this expectation and violates the principle that packing should be a transparent optimization that doesn't alter the record's identity or position.

## Fix

```diff
--- a/awkward/record.py
+++ b/awkward/record.py
@@ -196,7 +196,10 @@ class Record:
     def to_packed(self, recursive: bool = True) -> Self:
         if self._array.length is not unknown_length and self._array.length == 1:
             return Record(self._array.to_packed(recursive), self._at)
         else:
-            return Record(self._array[self._at : self._at + 1].to_packed(recursive), 0)
+            # Preserve the original position when packing
+            packed_array = self._array.to_packed(recursive)
+            return Record(packed_array, self._at)
```