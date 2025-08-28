#!/usr/bin/env python3
"""Deeper property-based tests for troposphere.cleanroomsml module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, assume, strategies as st, settings, example
import troposphere.cleanroomsml as crml
import troposphere


# Test missing required properties
def test_missing_required_properties():
    """Test that missing required properties are properly caught during validation"""
    
    # Test 1: Missing ColumnTypes in ColumnSchema
    try:
        schema = crml.ColumnSchema(
            ColumnName="test"
            # Missing ColumnTypes (required)
        )
        schema.to_dict()  # Trigger validation
        assert False, "ColumnSchema didn't catch missing required ColumnTypes"
    except (ValueError, AttributeError) as e:
        assert "ColumnTypes" in str(e) or "required" in str(e).lower()
    
    # Test 2: Missing TableName in GlueDataSource
    try:
        gds = crml.GlueDataSource(
            DatabaseName="db"
            # Missing TableName (required)
        )
        gds.to_dict()
        assert False, "GlueDataSource didn't catch missing required TableName"
    except (ValueError, AttributeError) as e:
        assert "TableName" in str(e) or "required" in str(e).lower()
    
    # Test 3: Missing TrainingData in TrainingDataset
    try:
        td = crml.TrainingDataset(
            title="Test",
            Name="TestDataset",
            RoleArn="arn:aws:iam::123456789012:role/TestRole"
            # Missing TrainingData (required)
        )
        td.to_dict()
        assert False, "TrainingDataset didn't catch missing required TrainingData"
    except (ValueError, AttributeError) as e:
        assert "TrainingData" in str(e) or "required" in str(e).lower()


# Test property mutation after creation
@given(
    initial_name=st.text(min_size=1, max_size=50),
    new_name=st.text(min_size=1, max_size=50)
)
def test_property_mutation(initial_name, new_name):
    """Test that properties can be mutated after object creation"""
    schema = crml.ColumnSchema(
        ColumnName=initial_name,
        ColumnTypes=["string"]
    )
    
    # Initial value
    assert schema.ColumnName == initial_name
    initial_dict = schema.to_dict()
    assert initial_dict["ColumnName"] == initial_name
    
    # Mutate the property
    schema.ColumnName = new_name
    
    # Check mutation worked
    assert schema.ColumnName == new_name
    new_dict = schema.to_dict()
    assert new_dict["ColumnName"] == new_name
    
    # Ensure the change persists through serialization
    reconstructed = crml.ColumnSchema.from_dict(None, new_dict)
    assert reconstructed.ColumnName == new_name


# Test Dataset Type validation
@given(
    dataset_type=st.text(min_size=1, max_size=50)
)
def test_dataset_type_values(dataset_type):
    """Test Dataset Type property accepts various values"""
    # The Type field likely has specific valid values in CloudFormation,
    # but the Python library might not validate them
    dataset = crml.Dataset(
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
        Type=dataset_type  # Could be anything - library might not validate
    )
    
    assert dataset.Type == dataset_type
    as_dict = dataset.to_dict()
    assert as_dict["Type"] == dataset_type


# Test deeply nested object equality and hashing
@given(
    data=st.data()
)
def test_deep_object_equality_and_hash(data):
    """Test equality and hashing for deeply nested objects"""
    
    # Generate random but valid components
    db_name = data.draw(st.text(min_size=1, max_size=30))
    table_name = data.draw(st.text(min_size=1, max_size=30))
    col_name = data.draw(st.text(min_size=1, max_size=30))
    col_types = data.draw(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3))
    
    # Create two identical objects
    def create_dataset():
        return crml.Dataset(
            InputConfig=crml.DatasetInputConfig(
                DataSource=crml.DataSource(
                    GlueDataSource=crml.GlueDataSource(
                        DatabaseName=db_name,
                        TableName=table_name
                    )
                ),
                Schema=[
                    crml.ColumnSchema(
                        ColumnName=col_name,
                        ColumnTypes=col_types
                    )
                ]
            ),
            Type="TRAINING"
        )
    
    ds1 = create_dataset()
    ds2 = create_dataset()
    
    # Test equality
    assert ds1 == ds2
    
    # Test that hash is consistent
    hash1 = hash(json.dumps(ds1.to_dict(), sort_keys=True))
    hash2 = hash(json.dumps(ds2.to_dict(), sort_keys=True))
    assert hash1 == hash2
    
    # Modify one and verify they're no longer equal
    ds2.Type = "VALIDATION"
    assert ds1 != ds2


# Test serialization with AWS Helper Functions (if supported)
def test_with_ref_and_getatt():
    """Test that objects handle AWS intrinsic functions"""
    # CloudFormation supports Ref and GetAtt functions
    # Let's see how the library handles them
    
    # Try using a Ref for a string property
    from troposphere import Ref
    
    try:
        schema = crml.ColumnSchema(
            ColumnName=Ref("MyParameter"),  # Using Ref instead of string
            ColumnTypes=["string"]
        )
        
        # This might work since troposphere supports AWSHelperFn
        as_dict = schema.to_dict()
        
        # Check that Ref is preserved in serialization
        assert "Ref" in str(as_dict["ColumnName"]) or isinstance(as_dict["ColumnName"], dict)
    except (TypeError, ValueError):
        # Library might not support Refs for all properties
        pass


# Test from_dict with invalid/malformed data
@given(
    malformed=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.none(), st.integers(), st.floats(), st.text()),
        min_size=0,
        max_size=5
    )
)
def test_from_dict_validation(malformed):
    """Test that from_dict properly validates input"""
    try:
        # Try to create object from potentially malformed dict
        obj = crml.ColumnSchema.from_dict(None, malformed)
        
        # If it succeeded, the data must have been valid somehow
        # Verify we can serialize it back
        obj.to_dict()
    except (ValueError, TypeError, AttributeError, KeyError):
        # Expected for malformed input
        pass


# Test object comparison with different types
@given(
    compare_with=st.one_of(
        st.integers(),
        st.floats(),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.text()),
        st.none()
    )
)
def test_equality_with_wrong_types(compare_with):
    """Test that objects don't equal non-objects"""
    schema = crml.ColumnSchema(
        ColumnName="test",
        ColumnTypes=["string"]
    )
    
    # Comparison with wrong type should return False or NotImplemented
    result = schema == compare_with
    assert result is False or result is NotImplemented
    
    # Not equal should work too
    result = schema != compare_with  
    assert result is True or result is NotImplemented


# Test property accessor edge cases
def test_property_accessors():
    """Test various property access patterns"""
    schema = crml.ColumnSchema(
        ColumnName="test",
        ColumnTypes=["string"]
    )
    
    # Test getting non-existent property
    try:
        _ = schema.NonExistentProperty
        assert False, "Accessing non-existent property should raise AttributeError"
    except AttributeError:
        pass  # Expected
    
    # Test setting non-existent property (might be allowed for custom resources)
    try:
        schema.CustomProperty = "value"
        # If this succeeds, it might be intentional for extensibility
        # But for our specific classes, it should fail
        assert False, "Setting non-existent property should raise AttributeError"
    except AttributeError:
        pass  # Expected for these resource types


# Test JSON serialization with various indentation/formatting
@given(
    indent=st.one_of(st.none(), st.integers(min_value=0, max_value=8)),
    sort_keys=st.booleans()
)
def test_json_formatting_options(indent, sort_keys):
    """Test that to_json respects formatting options"""
    schema = crml.ColumnSchema(
        ColumnName="test",
        ColumnTypes=["string", "integer"]
    )
    
    # Get JSON with specific formatting
    if indent is not None:
        json_str = schema.to_json(indent=indent, sort_keys=sort_keys)
    else:
        json_str = schema.to_json(sort_keys=sort_keys)
    
    # Verify it's valid JSON
    parsed = json.loads(json_str)
    
    # Verify content is correct
    assert parsed["ColumnName"] == "test"
    assert parsed["ColumnTypes"] == ["string", "integer"]
    
    # Check formatting hints (approximate)
    if indent and indent > 0:
        # Should have newlines if indented
        assert '\n' in json_str
    
    if sort_keys:
        # Keys should appear in sorted order
        keys_in_order = list(parsed.keys())
        assert keys_in_order == sorted(keys_in_order)


if __name__ == "__main__":
    print("Running deeper property tests for troposphere.cleanroomsml...")
    
    import pytest  
    pytest.main([__file__, "-v", "--tb=short"])