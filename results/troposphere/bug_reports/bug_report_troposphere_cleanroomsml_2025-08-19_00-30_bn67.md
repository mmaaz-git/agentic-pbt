# Bug Report: troposphere.cleanroomsml Tags Round-Trip Serialization Failure

**Target**: `troposphere.cleanroomsml.TrainingDataset`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The Tags property in TrainingDataset cannot survive a to_dict/from_dict round-trip due to type mismatch during deserialization.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.cleanroomsml as crml
from troposphere import Tags

@given(
    include_tags=st.booleans(),
    tag_key=st.text(min_size=1, max_size=20),
    tag_value=st.text(min_size=1, max_size=20)
)
def test_tags_round_trip(include_tags, tag_key, tag_value):
    """Test that TrainingDataset with Tags survives round-trip"""
    kwargs = {
        "Name": "TestDataset",
        "RoleArn": "arn:aws:iam::123456789012:role/TestRole",
        "TrainingData": [
            crml.Dataset(
                InputConfig=crml.DatasetInputConfig(
                    DataSource=crml.DataSource(
                        GlueDataSource=crml.GlueDataSource(
                            DatabaseName="db",
                            TableName="table"
                        )
                    ),
                    Schema=[
                        crml.ColumnSchema(
                            ColumnName="col",
                            ColumnTypes=["string"]
                        )
                    ]
                ),
                Type="TRAINING"
            )
        ]
    }
    
    if include_tags:
        kwargs["Tags"] = Tags({tag_key: tag_value})
    
    td = crml.TrainingDataset(title="Test", **kwargs)
    as_dict = td.to_dict()
    
    # This fails when Tags are included
    reconstructed = crml.TrainingDataset.from_dict("Test", as_dict["Properties"])
    assert td.to_dict() == reconstructed.to_dict()
```

**Failing input**: `include_tags=True, tag_key='Environment', tag_value='Test'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cleanroomsml as crml
from troposphere import Tags

td = crml.TrainingDataset(
    title="TestDataset",
    Name="MyDataset",
    RoleArn="arn:aws:iam::123456789012:role/TestRole",
    TrainingData=[
        crml.Dataset(
            InputConfig=crml.DatasetInputConfig(
                DataSource=crml.DataSource(
                    GlueDataSource=crml.GlueDataSource(
                        DatabaseName="test_db",
                        TableName="test_table"
                    )
                ),
                Schema=[
                    crml.ColumnSchema(
                        ColumnName="col1",
                        ColumnTypes=["string"]
                    )
                ]
            ),
            Type="TRAINING"
        )
    ],
    Tags=Tags(Environment="Test")
)

as_dict = td.to_dict()

reconstructed = crml.TrainingDataset.from_dict("TestDataset", as_dict["Properties"])
```

## Why This Is A Bug

The Tags object is serialized to a list of dictionaries `[{'Key': 'Environment', 'Value': 'Test'}]` but from_dict expects a Tags object type. This violates the round-trip property that `from_dict(to_dict(obj))` should reconstruct the original object.

## Fix

The from_dict method needs to handle Tags specially when reconstructing objects. When it encounters a list for the Tags property, it should reconstruct a Tags object from that list:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -374,6 +374,10 @@ class BaseAWSObject:
             prop_type = prop_attrs[0]
             value = kwargs[prop_name]
+            # Special handling for Tags
+            if prop_name == "Tags" and isinstance(value, list):
+                # Reconstruct Tags from list representation
+                value = Tags({item['Key']: item['Value'] for item in value})
             is_aws_object = is_aws_object_subclass(prop_type)
             if is_aws_object:
                 if not isinstance(value, collections.abc.Mapping):
```