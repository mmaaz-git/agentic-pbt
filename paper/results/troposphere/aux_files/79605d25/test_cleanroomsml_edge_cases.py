#!/usr/bin/env python3
"""Edge case property-based tests for troposphere.cleanroomsml module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, assume, strategies as st, settings, example
import troposphere.cleanroomsml as crml
import troposphere


# Test edge cases with empty strings and special characters
@given(
    empty_or_whitespace=st.sampled_from(["", " ", "  ", "\t", "\n", " \n\t "])
)
def test_empty_string_column_name(empty_or_whitespace):
    """Test that ColumnSchema handles empty/whitespace column names"""
    # CloudFormation typically doesn't accept empty strings for required properties
    # Let's see if the library validates this
    schema = crml.ColumnSchema(
        ColumnName=empty_or_whitespace,
        ColumnTypes=["string"]
    )
    # If it accepts empty strings, check serialization
    as_dict = schema.to_dict()
    assert "ColumnName" in as_dict
    assert as_dict["ColumnName"] == empty_or_whitespace


@given(
    special_chars=st.text(alphabet="!@#$%^&*(){}[]|\\:;\"'<>,.?/~`", min_size=1, max_size=10)
)
def test_special_characters_in_names(special_chars):
    """Test that special characters are handled in database/table names"""
    # AWS Glue has restrictions on special characters, but the library might not validate
    gds = crml.GlueDataSource(
        DatabaseName=f"db_{special_chars}",
        TableName=f"table_{special_chars}"
    )
    as_dict = gds.to_dict()
    assert as_dict["DatabaseName"] == f"db_{special_chars}"
    assert as_dict["TableName"] == f"table_{special_chars}"


@given(
    very_long_string=st.text(min_size=1000, max_size=10000)
)
def test_very_long_strings(very_long_string):
    """Test handling of very long strings in properties"""
    # CloudFormation has limits, but the library might not enforce them
    try:
        schema = crml.ColumnSchema(
            ColumnName=very_long_string,
            ColumnTypes=["string"]
        )
        # If it accepts it, verify serialization works
        as_dict = schema.to_dict()
        assert as_dict["ColumnName"] == very_long_string
    except Exception as e:
        # If there's a limit, it should raise a meaningful error
        assert "length" in str(e).lower() or "too long" in str(e).lower()


@given(
    column_types=st.lists(st.text(min_size=0, max_size=100), min_size=0, max_size=1000)
)
def test_column_types_edge_cases(column_types):
    """Test edge cases for ColumnTypes list"""
    # Test with empty list, very long list, empty strings in list
    if len(column_types) == 0:
        # Empty list might not be valid for ColumnTypes
        try:
            schema = crml.ColumnSchema(
                ColumnName="test",
                ColumnTypes=column_types
            )
            # If it accepts empty list, that might be a bug
            as_dict = schema.to_dict()
            assert as_dict["ColumnTypes"] == column_types
        except (ValueError, TypeError) as e:
            # Expected - empty list probably not valid
            pass
    else:
        schema = crml.ColumnSchema(
            ColumnName="test",
            ColumnTypes=column_types
        )
        assert schema.ColumnTypes == column_types


@given(
    datasets=st.lists(
        st.builds(
            lambda: crml.Dataset(
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
        ),
        min_size=0,
        max_size=10
    )
)
def test_training_dataset_empty_list(datasets):
    """Test TrainingDataset with empty or varying dataset lists"""
    if len(datasets) == 0:
        # Empty TrainingData list might not be valid
        try:
            td = crml.TrainingDataset(
                title="Test",
                Name="TestDataset",
                RoleArn="arn:aws:iam::123456789012:role/TestRole",
                TrainingData=datasets
            )
            # Empty list might be invalid
            td.to_dict()
        except (ValueError, TypeError) as e:
            # Expected if empty list is not allowed
            pass
    else:
        td = crml.TrainingDataset(
            title="Test",
            Name="TestDataset", 
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            TrainingData=datasets
        )
        assert len(td.TrainingData) == len(datasets)


@given(
    title=st.text(),
    valid_title=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=100)
)
def test_training_dataset_title_validation(title, valid_title):
    """Test that title validation works correctly"""
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
        Type="TRAINING"
    )
    
    # Test with potentially invalid title
    if title and not all(c.isalnum() for c in title):
        # Should raise ValueError for non-alphanumeric titles
        try:
            td = crml.TrainingDataset(
                title=title,
                Name="TestDataset",
                RoleArn="arn:aws:iam::123456789012:role/TestRole",
                TrainingData=[dataset]
            )
            # If it didn't raise, the title was somehow valid
            # Check if it's actually alphanumeric
            assert all(c.isalnum() for c in title)
        except ValueError as e:
            assert "alphanumeric" in str(e)
    
    # Test with valid title
    td_valid = crml.TrainingDataset(
        title=valid_title,
        Name="TestDataset",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        TrainingData=[dataset]
    )
    assert td_valid.title == valid_title


@given(
    include_optional=st.booleans(),
    catalog_id=st.one_of(st.none(), st.text(min_size=1, max_size=20))
)
def test_optional_property_handling(include_optional, catalog_id):
    """Test that optional properties are handled correctly in serialization"""
    kwargs = {
        "DatabaseName": "test_db",
        "TableName": "test_table"
    }
    
    if include_optional and catalog_id is not None:
        kwargs["CatalogId"] = catalog_id
    
    gds = crml.GlueDataSource(**kwargs)
    as_dict = gds.to_dict()
    
    # Check that optional property is included only when provided
    if include_optional and catalog_id is not None:
        assert "CatalogId" in as_dict
        assert as_dict["CatalogId"] == catalog_id
    else:
        # Optional property might or might not be in dict when not provided
        if "CatalogId" in as_dict:
            # If it's there, it should be None or empty
            assert as_dict["CatalogId"] in [None, ""]


@given(
    wrong_type_for_list=st.one_of(
        st.integers(),
        st.floats(),
        st.booleans(),
        st.dictionaries(st.text(), st.text()),
        st.text()
    )
)
def test_wrong_type_for_training_data(wrong_type_for_list):
    """Test that TrainingData validates list type properly"""
    try:
        td = crml.TrainingDataset(
            title="Test",
            Name="TestDataset",
            RoleArn="arn:aws:iam::123456789012:role/TestRole",
            TrainingData=wrong_type_for_list  # Should be a list
        )
        # If it accepts non-list, that's likely a bug
        assert False, f"TrainingDataset accepted non-list TrainingData: {type(wrong_type_for_list)}"
    except (TypeError, AttributeError) as e:
        # Expected - should reject non-list
        pass


@given(
    num_schemas=st.integers(min_value=0, max_value=100)
)
def test_dataset_input_config_many_schemas(num_schemas):
    """Test DatasetInputConfig with varying numbers of schemas"""
    schemas = []
    for i in range(num_schemas):
        schemas.append(
            crml.ColumnSchema(
                ColumnName=f"col_{i}",
                ColumnTypes=["string", "integer"]
            )
        )
    
    if num_schemas == 0:
        # Empty schema list might not be valid
        try:
            config = crml.DatasetInputConfig(
                DataSource=crml.DataSource(
                    GlueDataSource=crml.GlueDataSource(
                        DatabaseName="db",
                        TableName="table"
                    )
                ),
                Schema=schemas
            )
            # If it accepts empty schema, verify
            assert len(config.Schema) == 0
        except (ValueError, TypeError):
            # Expected if empty schema is invalid
            pass
    else:
        config = crml.DatasetInputConfig(
            DataSource=crml.DataSource(
                GlueDataSource=crml.GlueDataSource(
                    DatabaseName="db",
                    TableName="table"
                )
            ),
            Schema=schemas
        )
        assert len(config.Schema) == num_schemas
        
        # Verify round-trip
        as_dict = config.to_dict()
        assert len(as_dict["Schema"]) == num_schemas


# Test with None values for required properties
def test_none_for_required_properties():
    """Test that None is properly rejected for required properties"""
    # Test ColumnSchema with None
    try:
        schema = crml.ColumnSchema(
            ColumnName=None,  # Required property
            ColumnTypes=["string"]
        )
        # Should not accept None for required property
        schema.to_dict()  # Trigger validation
        assert False, "ColumnSchema accepted None for required ColumnName"
    except (TypeError, ValueError):
        pass  # Expected
    
    # Test GlueDataSource with None
    try:
        gds = crml.GlueDataSource(
            DatabaseName=None,  # Required property
            TableName="table"
        )
        gds.to_dict()
        assert False, "GlueDataSource accepted None for required DatabaseName"
    except (TypeError, ValueError):
        pass  # Expected


# Test Unicode and international characters
@given(
    unicode_text=st.text(alphabet=st.characters(min_codepoint=0x1F300, max_codepoint=0x1F9FF), min_size=1, max_size=10)
)
def test_unicode_characters(unicode_text):
    """Test handling of Unicode/emoji characters"""
    # CloudFormation might have issues with certain Unicode characters
    schema = crml.ColumnSchema(
        ColumnName=f"col_{unicode_text}",
        ColumnTypes=["string"]
    )
    as_dict = schema.to_dict()
    assert as_dict["ColumnName"] == f"col_{unicode_text}"
    
    # Test JSON serialization with Unicode
    as_json = json.dumps(as_dict, ensure_ascii=False)
    from_json = json.loads(as_json)
    assert from_json == as_dict


if __name__ == "__main__":
    print("Running edge case tests for troposphere.cleanroomsml...")
    
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])