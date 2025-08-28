#!/usr/bin/env python3
"""Property-based tests for troposphere.cleanroomsml module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, assume, strategies as st, settings
import troposphere.cleanroomsml as crml


# Strategy for valid CloudFormation names (alphanumeric only)
valid_cf_names = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=100)

# Strategy for column names and types
column_names = st.text(min_size=1, max_size=50)
column_types = st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)

# Strategy for database/table names
db_table_names = st.text(min_size=1, max_size=100)

# Strategy for ARNs
arns = st.text(min_size=20, max_size=200).map(lambda s: f"arn:aws:iam::123456789012:role/{s}")

# Strategy for catalog IDs
catalog_ids = st.text(alphabet=st.characters(whitelist_categories=("Nd",)), min_size=12, max_size=12)


def create_column_schema(name, types):
    """Helper to create ColumnSchema objects"""
    return crml.ColumnSchema(
        ColumnName=name,
        ColumnTypes=types
    )


def create_glue_data_source(database, table, catalog_id=None):
    """Helper to create GlueDataSource objects"""
    kwargs = {
        "DatabaseName": database,
        "TableName": table
    }
    if catalog_id is not None:
        kwargs["CatalogId"] = catalog_id
    return crml.GlueDataSource(**kwargs)


# Test 1: Round-trip property for ColumnSchema - to_dict and from_dict
@given(
    name=column_names,
    types=column_types
)
def test_column_schema_round_trip(name, types):
    """Test that ColumnSchema survives to_dict/from_dict round trip"""
    original = crml.ColumnSchema(
        ColumnName=name,
        ColumnTypes=types
    )
    
    # Convert to dict and back
    as_dict = original.to_dict()
    reconstructed = crml.ColumnSchema.from_dict(None, as_dict)
    
    # They should be equal
    assert original.to_dict() == reconstructed.to_dict()
    assert original == reconstructed


# Test 2: Round-trip property for GlueDataSource with optional CatalogId
@given(
    database=db_table_names,
    table=db_table_names,
    include_catalog=st.booleans(),
    catalog=catalog_ids
)
def test_glue_data_source_round_trip(database, table, include_catalog, catalog):
    """Test that GlueDataSource survives to_dict/from_dict round trip"""
    kwargs = {
        "DatabaseName": database,
        "TableName": table
    }
    if include_catalog:
        kwargs["CatalogId"] = catalog
    
    original = crml.GlueDataSource(**kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    reconstructed = crml.GlueDataSource.from_dict(None, as_dict)
    
    # They should be equal
    assert original.to_dict() == reconstructed.to_dict()
    assert original == reconstructed


# Test 3: Required properties validation for TrainingDataset
@given(
    name=valid_cf_names,
    role_arn=arns,
    description=st.one_of(st.none(), st.text(min_size=1, max_size=200)),
    include_description=st.booleans()
)
def test_training_dataset_required_properties(name, role_arn, description, include_description):
    """Test that TrainingDataset validates required properties correctly"""
    # Create a minimal valid dataset
    dataset = crml.Dataset(
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
    
    kwargs = {
        "Name": name,
        "RoleArn": role_arn,
        "TrainingData": [dataset]
    }
    
    if include_description and description:
        kwargs["Description"] = description
    
    # This should work - all required properties are present
    td = crml.TrainingDataset(title="TestDataset", **kwargs)
    
    # Validation should pass
    td.to_dict()  # This triggers validation
    
    # The object should have the expected properties
    assert td.Name == name
    assert td.RoleArn == role_arn
    assert len(td.TrainingData) == 1
    if include_description and description:
        assert td.Description == description


# Test 4: JSON serialization round-trip
@given(
    db_name=db_table_names,
    table_name=db_table_names,
    col_name=column_names,
    col_types=column_types
)
def test_json_serialization_round_trip(db_name, table_name, col_name, col_types):
    """Test that objects survive JSON serialization"""
    # Create a complex nested structure
    ds = crml.DataSource(
        GlueDataSource=crml.GlueDataSource(
            DatabaseName=db_name,
            TableName=table_name
        )
    )
    
    # Convert to JSON and back
    as_dict = ds.to_dict()
    as_json = json.dumps(as_dict)
    from_json = json.loads(as_json)
    
    # Should be identical
    assert as_dict == from_json
    
    # Should be able to reconstruct from the JSON-loaded dict
    reconstructed = crml.DataSource.from_dict(None, from_json)
    assert ds == reconstructed


# Test 5: Property type validation - lists must be lists
@given(
    single_type=st.text(min_size=1, max_size=20),
    list_of_types=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
)
def test_column_schema_types_must_be_list(single_type, list_of_types):
    """Test that ColumnTypes property properly validates list type"""
    # This should work - ColumnTypes is a list
    schema = crml.ColumnSchema(
        ColumnName="test",
        ColumnTypes=list_of_types
    )
    assert schema.ColumnTypes == list_of_types
    
    # This should fail - ColumnTypes must be a list
    try:
        bad_schema = crml.ColumnSchema(
            ColumnName="test",
            ColumnTypes=single_type  # Not a list!
        )
        # If we get here, it means the validation failed to catch the error
        assert False, f"Expected TypeError but ColumnSchema accepted non-list ColumnTypes: {single_type}"
    except TypeError as e:
        # Expected behavior - should reject non-list
        assert "ColumnTypes" in str(e) or "list" in str(e).lower()


# Test 6: Dataset nesting and complex object equality
@given(
    db1=db_table_names,
    db2=db_table_names,
    table1=db_table_names,
    table2=db_table_names,
    same_values=st.booleans()
)
def test_complex_object_equality(db1, db2, table1, table2, same_values):
    """Test equality for complex nested objects"""
    if same_values:
        db2, table2 = db1, table1
    
    ds1 = crml.Dataset(
        InputConfig=crml.DatasetInputConfig(
            DataSource=crml.DataSource(
                GlueDataSource=crml.GlueDataSource(
                    DatabaseName=db1,
                    TableName=table1
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
    
    ds2 = crml.Dataset(
        InputConfig=crml.DatasetInputConfig(
            DataSource=crml.DataSource(
                GlueDataSource=crml.GlueDataSource(
                    DatabaseName=db2,
                    TableName=table2
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
    
    if same_values:
        assert ds1 == ds2
        assert ds1.to_dict() == ds2.to_dict()
    else:
        # With high probability they should be different
        # (unless db1==db2 and table1==table2 by chance)
        if db1 != db2 or table1 != table2:
            assert ds1 != ds2
            assert ds1.to_dict() != ds2.to_dict()


# Test 7: TrainingDataset accepts multiple datasets
@given(
    num_datasets=st.integers(min_value=1, max_value=5),
    dataset_types=st.lists(st.sampled_from(["TRAINING", "VALIDATION", "TEST"]), min_size=1, max_size=5)
)
def test_training_dataset_multiple_datasets(num_datasets, dataset_types):
    """Test that TrainingDataset correctly handles multiple datasets"""
    # Ensure we have the right number of types
    while len(dataset_types) < num_datasets:
        dataset_types.append("TRAINING")
    dataset_types = dataset_types[:num_datasets]
    
    datasets = []
    for i, dtype in enumerate(dataset_types):
        ds = crml.Dataset(
            InputConfig=crml.DatasetInputConfig(
                DataSource=crml.DataSource(
                    GlueDataSource=crml.GlueDataSource(
                        DatabaseName=f"db_{i}",
                        TableName=f"table_{i}"
                    )
                ),
                Schema=[
                    crml.ColumnSchema(
                        ColumnName=f"col_{i}",
                        ColumnTypes=["string"]
                    )
                ]
            ),
            Type=dtype
        )
        datasets.append(ds)
    
    td = crml.TrainingDataset(
        title="MultiDataset",
        Name="TestMultiDataset",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        TrainingData=datasets
    )
    
    # Should have all datasets
    assert len(td.TrainingData) == num_datasets
    
    # Round trip should preserve all datasets
    as_dict = td.to_dict()
    assert len(as_dict["Properties"]["TrainingData"]) == num_datasets
    
    # Each dataset should be preserved correctly
    for i, ds_dict in enumerate(as_dict["Properties"]["TrainingData"]):
        assert ds_dict["Type"] == dataset_types[i]
        assert ds_dict["InputConfig"]["DataSource"]["GlueDataSource"]["DatabaseName"] == f"db_{i}"


if __name__ == "__main__":
    print("Running property-based tests for troposphere.cleanroomsml...")
    
    # Run with more examples for thoroughness
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])