#!/usr/bin/env python3
"""Comprehensive property-based tests to find real bugs in troposphere.cleanroomsml"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import copy
from hypothesis import given, assume, strategies as st, settings, reproduce_failure
import troposphere.cleanroomsml as crml
import troposphere


# Test case sensitivity in property names
def test_case_sensitive_properties():
    """Test that property names are case-sensitive as they should be"""
    
    # CloudFormation is case-sensitive for property names
    # Let's verify the library handles this correctly
    
    try:
        # Try wrong case for ColumnName
        schema = crml.ColumnSchema(
            columnname="test",  # Wrong case!
            ColumnTypes=["string"]
        )
        # If this works, there's a bug - property names should be case-sensitive
        assert False, "Library accepted wrong case 'columnname' instead of 'ColumnName'"
    except (AttributeError, TypeError) as e:
        # Expected - should reject wrong case
        pass
    
    try:
        # Try wrong case for ColumnTypes
        schema = crml.ColumnSchema(
            ColumnName="test",
            columntypes=["string"]  # Wrong case!
        )
        assert False, "Library accepted wrong case 'columntypes' instead of 'ColumnTypes'"
    except (AttributeError, TypeError):
        pass


# Test duplicate property assignments
def test_duplicate_property_handling():
    """Test how the library handles duplicate property assignments"""
    
    # What happens if we pass the same property twice?
    # Python will use the last value, but let's verify
    schema = crml.ColumnSchema(
        ColumnName="first",
        ColumnTypes=["string"],
        # Can't really pass duplicates in kwargs, Python handles that
    )
    
    # But we can test setting a property multiple times
    schema.ColumnName = "second"
    schema.ColumnName = "third"
    
    assert schema.ColumnName == "third"
    as_dict = schema.to_dict()
    assert as_dict["ColumnName"] == "third"


# Test mixing property types incorrectly
@given(
    wrong_glue_ds=st.one_of(
        st.text(),
        st.integers(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_wrong_nested_object_types(wrong_glue_ds):
    """Test that nested object properties validate their types"""
    
    # DataSource expects a GlueDataSource object, not other types
    try:
        ds = crml.DataSource(
            GlueDataSource=wrong_glue_ds  # Wrong type!
        )
        # If it accepts wrong type, that's a bug
        as_dict = ds.to_dict()
        
        # It might convert dict to object automatically
        if isinstance(wrong_glue_ds, dict):
            # This could be valid if dict has right structure
            pass
        else:
            assert False, f"DataSource accepted wrong type for GlueDataSource: {type(wrong_glue_ds)}"
    except (TypeError, ValueError, AttributeError):
        # Expected - should reject wrong types
        pass


# Test validation toggling
def test_validation_on_off():
    """Test that validation can be turned on/off"""
    
    # Create object missing required property
    schema = crml.ColumnSchema(
        ColumnName="test"
        # Missing required ColumnTypes
    )
    
    # With validation off, to_dict should work despite missing required field
    schema_no_val = schema.no_validation()
    try:
        result = schema_no_val.to_dict(validation=False)
        # Should work with validation off
        assert "ColumnName" in result
    except ValueError:
        # If it still validates, that's unexpected
        assert False, "no_validation() didn't disable validation"
    
    # With validation on, should fail
    try:
        result = schema.to_dict(validation=True)
        assert False, "Validation didn't catch missing required property"
    except ValueError:
        pass  # Expected


# Test deeply nested round-trips with all optional fields
@given(
    include_catalog=st.booleans(),
    catalog_id=st.text(min_size=1, max_size=20) if True else st.none(),
    include_description=st.booleans(), 
    description=st.text(min_size=1, max_size=200) if True else st.none(),
    include_tags=st.booleans(),
    num_datasets=st.integers(min_value=1, max_value=3),
    num_schemas_per_dataset=st.integers(min_value=1, max_value=3)
)
def test_complete_object_round_trip(
    include_catalog, catalog_id,
    include_description, description,
    include_tags,
    num_datasets, num_schemas_per_dataset
):
    """Test complete round-trip with all fields populated"""
    
    # Build complete TrainingDataset with all optional fields
    datasets = []
    for i in range(num_datasets):
        schemas = []
        for j in range(num_schemas_per_dataset):
            schemas.append(crml.ColumnSchema(
                ColumnName=f"col_{i}_{j}",
                ColumnTypes=[f"type_{k}" for k in range(min(3, j+1))]
            ))
        
        glue_kwargs = {
            "DatabaseName": f"db_{i}",
            "TableName": f"table_{i}"
        }
        if include_catalog and catalog_id:
            glue_kwargs["CatalogId"] = f"{catalog_id}_{i}"
        
        datasets.append(crml.Dataset(
            InputConfig=crml.DatasetInputConfig(
                DataSource=crml.DataSource(
                    GlueDataSource=crml.GlueDataSource(**glue_kwargs)
                ),
                Schema=schemas
            ),
            Type=["TRAINING", "VALIDATION", "TEST"][i % 3]
        ))
    
    td_kwargs = {
        "Name": "CompleteDataset",
        "RoleArn": "arn:aws:iam::123456789012:role/TestRole",
        "TrainingData": datasets
    }
    
    if include_description and description:
        td_kwargs["Description"] = description
    
    if include_tags:
        # Tags might need special handling
        from troposphere import Tags
        td_kwargs["Tags"] = Tags(TestTag="TestValue")
    
    td = crml.TrainingDataset(title="CompleteTest", **td_kwargs)
    
    # Convert to dict
    as_dict = td.to_dict()
    
    # Recreate from dict
    reconstructed = crml.TrainingDataset.from_dict("CompleteTest", as_dict["Properties"])
    
    # Should be equal
    assert td.to_dict() == reconstructed.to_dict()


# Test that resource_type is set correctly
def test_resource_type():
    """Test that resource_type is correctly set for TrainingDataset"""
    
    td = crml.TrainingDataset(
        title="Test",
        Name="TestDataset",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        TrainingData=[
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
    )
    
    # Check resource type
    assert td.resource_type == "AWS::CleanRoomsML::TrainingDataset"
    
    # Check it's in the serialized output
    as_dict = td.to_dict()
    assert as_dict["Type"] == "AWS::CleanRoomsML::TrainingDataset"


# Test property deletion/removal
def test_property_deletion():
    """Test that properties can be deleted/removed"""
    
    gds = crml.GlueDataSource(
        DatabaseName="db",
        TableName="table",
        CatalogId="123456789012"  # Optional property
    )
    
    # Verify it's set
    assert gds.CatalogId == "123456789012"
    as_dict = gds.to_dict()
    assert as_dict.get("CatalogId") == "123456789012"
    
    # Try to delete it
    try:
        del gds.CatalogId
        # If deletion works, verify it's gone
        as_dict_after = gds.to_dict()
        assert "CatalogId" not in as_dict_after
    except (AttributeError, TypeError):
        # Deletion might not be supported
        pass


# Test integer where string expected
@given(
    int_value=st.integers()
)
def test_integer_for_string_property(int_value):
    """Test that integer values are handled for string properties"""
    
    # ColumnName expects a string, but what if we pass an integer?
    try:
        schema = crml.ColumnSchema(
            ColumnName=int_value,  # Integer instead of string!
            ColumnTypes=["string"]
        )
        
        # If it accepts it, how is it stored?
        name = schema.ColumnName
        
        # It might auto-convert to string
        if isinstance(name, str):
            assert name == str(int_value)
        elif isinstance(name, int):
            # Stored as-is
            assert name == int_value
        
        # Check serialization
        as_dict = schema.to_dict()
        # CloudFormation would expect string
        
    except (TypeError, ValueError):
        # Expected - should reject wrong type
        pass


# Test __eq__ and __ne__ implementation
@given(
    name1=st.text(min_size=1, max_size=20),
    name2=st.text(min_size=1, max_size=20),
    types1=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3),
    types2=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3)
)
def test_equality_implementation(name1, name2, types1, types2):
    """Test that equality is properly implemented"""
    
    schema1 = crml.ColumnSchema(ColumnName=name1, ColumnTypes=types1)
    schema2 = crml.ColumnSchema(ColumnName=name2, ColumnTypes=types2)
    schema1_copy = crml.ColumnSchema(ColumnName=name1, ColumnTypes=types1)
    
    # Reflexive: x == x
    assert schema1 == schema1
    
    # Symmetric: x == y implies y == x
    if schema1 == schema2:
        assert schema2 == schema1
    
    # Transitive: x == y and y == z implies x == z
    if schema1 == schema1_copy:
        assert schema1_copy == schema1
    
    # Consistent with !=
    assert (schema1 == schema2) == (not (schema1 != schema2))
    
    # Equal objects should have same dict representation
    if schema1 == schema1_copy:
        assert schema1.to_dict() == schema1_copy.to_dict()


# Test CloudFormation intrinsic functions in all positions
def test_intrinsic_functions_comprehensive():
    """Test AWS intrinsic functions in various property positions"""
    from troposphere import Ref, GetAtt, Sub, Join
    
    # Test in different property types
    test_cases = [
        # String property with Ref
        lambda: crml.ColumnSchema(
            ColumnName=Ref("MyParameter"),
            ColumnTypes=["string"]
        ),
        
        # String property with Sub
        lambda: crml.GlueDataSource(
            DatabaseName=Sub("db-${AWS::StackName}"),
            TableName="table"
        ),
        
        # List property with intrinsic function (might not work)
        lambda: crml.ColumnSchema(
            ColumnName="test",
            ColumnTypes=Ref("MyTypesList")  # Ref to a list parameter
        ),
    ]
    
    for i, test_func in enumerate(test_cases):
        try:
            obj = test_func()
            as_dict = obj.to_dict()
            # If it works, verify the function is preserved
            # The dict should contain the intrinsic function structure
        except (TypeError, ValueError):
            # Some positions might not accept intrinsic functions
            pass


# Test maximum nesting depth
@given(
    depth=st.integers(min_value=1, max_value=10)
)
def test_serialization_depth(depth):
    """Test that deeply nested structures serialize correctly"""
    
    # Create nested structure with variable depth
    # (Though our schema has fixed depth, we can test multiple datasets)
    datasets = []
    for i in range(min(depth, 5)):  # Cap at 5 to avoid memory issues
        datasets.append(
            crml.Dataset(
                InputConfig=crml.DatasetInputConfig(
                    DataSource=crml.DataSource(
                        GlueDataSource=crml.GlueDataSource(
                            DatabaseName=f"db_{i}",
                            TableName=f"table_{i}"
                        )
                    ),
                    Schema=[
                        crml.ColumnSchema(
                            ColumnName=f"col_{j}",
                            ColumnTypes=[f"type_{k}" for k in range(3)]
                        )
                        for j in range(3)
                    ]
                ),
                Type="TRAINING"
            )
        )
    
    if datasets:
        td = crml.TrainingDataset(
            title="DeepTest",
            Name="DeepDataset",
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            TrainingData=datasets
        )
        
        # Test serialization
        as_json = td.to_json()
        
        # Parse back
        parsed = json.loads(as_json)
        
        # Verify structure
        assert len(parsed["Properties"]["TrainingData"]) == len(datasets)


if __name__ == "__main__":
    print("Running comprehensive tests for troposphere.cleanroomsml...")
    
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])