# Bug Report: troposphere.route53recoveryreadiness Round-trip Serialization Failure

**Target**: `troposphere.route53recoveryreadiness.Cell`, `ResourceSet`, `RecoveryGroup`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict()` class method cannot deserialize the output of `to_dict()`, breaking the expected round-trip serialization property for AWS CloudFormation resource classes.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.route53recoveryreadiness import Cell

@given(
    cell_name=st.text(min_size=1, max_size=100),
    cells=st.lists(st.text(min_size=1, max_size=100), max_size=5),
)
def test_cell_round_trip_serialization(cell_name, cells):
    original = Cell(
        title="TestCell",
        CellName=cell_name,
        Cells=cells,
    )
    
    dict_repr = original.to_dict()
    reconstructed = Cell.from_dict("TestCell", dict_repr)
    
    assert reconstructed.to_dict() == dict_repr
```

**Failing input**: `cell_name='0', cells=[]`

## Reproducing the Bug

```python
from troposphere.route53recoveryreadiness import Cell

cell = Cell(
    title="TestCell", 
    CellName="MyCell",
    Cells=["Cell1", "Cell2"],
)

dict_repr = cell.to_dict()
print(dict_repr)

reconstructed = Cell.from_dict("TestCell", dict_repr)
```

## Why This Is A Bug

The `to_dict()` method returns a nested structure like `{'Properties': {...}, 'Type': '...'}`, but `from_dict()` expects to receive just the Properties dictionary directly. This violates the expected contract that `from_dict(to_dict(obj))` should reconstruct the original object.

## Fix

The `from_dict()` method should handle the nested structure returned by `to_dict()`:

```diff
 @classmethod
 def from_dict(cls, title, d):
+    # Handle both nested and flat dictionary structures
+    if "Properties" in d and isinstance(d["Properties"], dict):
+        # Extract Properties from nested structure
+        return cls._from_dict(title, **d["Properties"])
     return cls._from_dict(title, **d)
```