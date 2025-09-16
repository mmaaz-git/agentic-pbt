# Bug Report: troposphere.lakeformation Round-Trip Serialization Failure

**Target**: `troposphere.lakeformation.DataCellsFilter.from_dict`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `from_dict` method fails to properly deserialize the output of `to_dict`, breaking round-trip serialization for AWS::LakeFormation resources.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from hypothesis.strategies import composite
from troposphere.lakeformation import DataCellsFilter

@composite
def valid_datacellsfilter_data(draw):
    return {
        "DatabaseName": draw(st.text(min_size=1, max_size=20)),
        "Name": draw(st.text(min_size=1, max_size=20)),
        "TableCatalogId": draw(st.text(min_size=1, max_size=20)),
        "TableName": draw(st.text(min_size=1, max_size=20)),
    }

@given(valid_datacellsfilter_data())
def test_datacellsfilter_roundtrip(data):
    dcf = DataCellsFilter("TestFilter", **data)
    dict_repr = dcf.to_dict()
    reconstructed = DataCellsFilter.from_dict("TestFilter2", dict_repr)
    assert reconstructed.to_dict() == dict_repr
```

**Failing input**: Any valid DataCellsFilter configuration

## Reproducing the Bug

```python
from troposphere.lakeformation import DataCellsFilter

dcf = DataCellsFilter(
    "MyFilter",
    DatabaseName="mydb",
    Name="myfilter",
    TableCatalogId="12345",
    TableName="mytable"
)

dict_repr = dcf.to_dict()
print(dict_repr)
# {'Properties': {'DatabaseName': 'mydb', ...}, 'Type': 'AWS::LakeFormation::DataCellsFilter'}

reconstructed = DataCellsFilter.from_dict("MyFilter2", dict_repr)
# AttributeError: Object type DataCellsFilter does not have a Properties property.
```

## Why This Is A Bug

The `to_dict()` method produces a dictionary with a "Properties" key containing the resource properties, but `from_dict()` cannot parse this structure. This breaks a fundamental expectation that serialization and deserialization should be inverse operations.

## Fix

The `from_dict` method needs to handle the "Properties" key that `to_dict` generates. The issue is in the base class implementation which doesn't recognize "Properties" as a valid attribute. The fix would involve modifying the `_from_dict` method to extract properties from the "Properties" key when present:

```diff
@classmethod
def from_dict(cls, title, d):
+    # Extract properties from the Properties key if present
+    if "Properties" in d and "Type" in d:
+        # This is output from to_dict()
+        return cls._from_dict(title, **d["Properties"])
    return cls._from_dict(title, **d)
```