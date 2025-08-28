#!/usr/bin/env python3
"""Property-based tests for troposphere.iottwinmaker module."""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import troposphere
from troposphere import iottwinmaker
from troposphere.validators.iottwinmaker import validate_listvalue, validate_nestedtypel


# Strategy for generating valid strings that troposphere expects
valid_string = st.text(min_size=1, max_size=50).filter(lambda x: x.strip())

# Strategy for alphanumeric titles
alphanumeric_title = st.from_regex(r"^[a-zA-Z0-9]{1,50}$", fullmatch=True)


# Test 1: validate_listvalue should properly validate lists of DataValue
@given(st.data())
def test_validate_listvalue_type_checking(data):
    """Test that validate_listvalue properly validates its input types."""
    # Test with non-list input - should raise TypeError
    non_list = data.draw(st.one_of(
        st.integers(),
        st.text(),
        st.dictionaries(st.text(), st.text()),
        st.booleans()
    ))
    
    try:
        validate_listvalue(non_list)
        assert False, "Should have raised TypeError for non-list input"
    except TypeError as e:
        assert "ListValue must be a list" in str(e)


@given(st.lists(st.integers()))
def test_validate_listvalue_with_invalid_items(invalid_list):
    """Test that validate_listvalue rejects lists with invalid item types."""
    assume(len(invalid_list) > 0)  # Only test non-empty lists
    
    try:
        validate_listvalue(invalid_list)
        assert False, "Should have raised TypeError for list with invalid items"
    except TypeError as e:
        assert "ListValue must contain DataValue or AWSHelperFn" in str(e)


# Test 2: DataValue round-trip property
@given(
    boolean_val=st.booleans(),
    double_val=st.floats(allow_nan=False, allow_infinity=False),
    integer_val=st.integers(min_value=-2**31, max_value=2**31-1),
    string_val=valid_string,
    expression=valid_string
)
def test_datavalue_field_consistency(boolean_val, double_val, integer_val, string_val, expression):
    """Test that DataValue objects preserve their field values correctly."""
    # Create DataValue with various field types
    data_val1 = iottwinmaker.DataValue(BooleanValue=boolean_val)
    data_val2 = iottwinmaker.DataValue(DoubleValue=double_val)
    data_val3 = iottwinmaker.DataValue(IntegerValue=integer_val)
    data_val4 = iottwinmaker.DataValue(StringValue=string_val)
    data_val5 = iottwinmaker.DataValue(Expression=expression)
    
    # Check that values are preserved in to_dict()
    assert data_val1.to_dict()["BooleanValue"] == boolean_val
    assert data_val2.to_dict()["DoubleValue"] == double_val
    assert data_val3.to_dict()["IntegerValue"] == integer_val
    assert data_val4.to_dict()["StringValue"] == string_val
    assert data_val5.to_dict()["Expression"] == expression


# Test 3: Round-trip property for Entity objects
@given(
    entity_name=valid_string,
    workspace_id=valid_string,
    description=st.one_of(st.none(), valid_string),
    entity_id=st.one_of(st.none(), valid_string)
)
def test_entity_round_trip(entity_name, workspace_id, description, entity_id):
    """Test that Entity objects can be serialized and deserialized correctly."""
    # Create an Entity
    kwargs = {
        "EntityName": entity_name,
        "WorkspaceId": workspace_id
    }
    if description:
        kwargs["Description"] = description
    if entity_id:
        kwargs["EntityId"] = entity_id
    
    entity = iottwinmaker.Entity("TestEntity", **kwargs)
    
    # Convert to dict and back
    entity_dict = entity.to_dict(validation=False)
    
    # Verify required properties are preserved
    props = entity_dict["Properties"]
    assert props["EntityName"] == entity_name
    assert props["WorkspaceId"] == workspace_id
    if description:
        assert props["Description"] == description
    if entity_id:
        assert props["EntityId"] == entity_id


# Test 4: ComponentType with required properties
@given(
    component_type_id=valid_string,
    workspace_id=valid_string,
    is_singleton=st.booleans()
)
def test_componenttype_required_properties(component_type_id, workspace_id, is_singleton):
    """Test that ComponentType correctly handles required properties."""
    # Create with all required properties - should work
    ct = iottwinmaker.ComponentType(
        "TestComponentType",
        ComponentTypeId=component_type_id,
        WorkspaceId=workspace_id,
        IsSingleton=is_singleton
    )
    
    # Verify properties are set correctly
    assert ct.ComponentTypeId == component_type_id
    assert ct.WorkspaceId == workspace_id
    assert ct.IsSingleton == is_singleton
    
    # Test validation - missing required property should fail
    try:
        ct_invalid = iottwinmaker.ComponentType(
            "TestComponentType2",
            ComponentTypeId=component_type_id
            # Missing WorkspaceId
        )
        ct_invalid.to_dict()  # This triggers validation
        assert False, "Should have raised ValueError for missing required property"
    except ValueError as e:
        assert "required" in str(e).lower()


# Test 5: Test Scene object with capabilities list
@given(
    scene_id=valid_string,
    content_location=valid_string,
    workspace_id=valid_string,
    capabilities=st.lists(valid_string, min_size=0, max_size=10)
)
def test_scene_capabilities_list(scene_id, content_location, workspace_id, capabilities):
    """Test that Scene correctly handles the Capabilities list property."""
    scene = iottwinmaker.Scene(
        "TestScene",
        SceneId=scene_id,
        ContentLocation=content_location,
        WorkspaceId=workspace_id,
        Capabilities=capabilities
    )
    
    scene_dict = scene.to_dict(validation=False)
    
    # Verify list is preserved
    if capabilities:
        assert scene_dict["Properties"]["Capabilities"] == capabilities
    
    # Check that setting non-list raises error
    try:
        scene2 = iottwinmaker.Scene(
            "TestScene2",
            SceneId=scene_id,
            ContentLocation=content_location,
            WorkspaceId=workspace_id,
            Capabilities="not_a_list"  # Should be a list
        )
        assert False, "Should have raised error for non-list Capabilities"
    except Exception:
        pass  # Expected to fail


# Test 6: Test Workspace title validation
@given(
    valid_title=alphanumeric_title,
    invalid_title=st.text(min_size=1).filter(lambda x: not x.isalnum())
)
def test_workspace_title_validation(valid_title, invalid_title):
    """Test that Workspace title validation works correctly."""
    # Valid title should work
    workspace = iottwinmaker.Workspace(
        valid_title,
        Role="test-role",
        S3Location="s3://bucket/path",
        WorkspaceId="test-workspace"
    )
    workspace.to_dict(validation=False)  # Should not raise
    
    # Invalid title should fail
    try:
        workspace2 = iottwinmaker.Workspace(
            invalid_title,
            Role="test-role",
            S3Location="s3://bucket/path",
            WorkspaceId="test-workspace"
        )
        assert False, f"Should have raised error for invalid title: {invalid_title}"
    except ValueError as e:
        assert "not alphanumeric" in str(e)


# Test 7: Test equality and hash consistency for Entity objects
@given(
    entity_name1=valid_string,
    entity_name2=valid_string,
    workspace_id=valid_string
)
def test_entity_equality_and_hash(entity_name1, entity_name2, workspace_id):
    """Test that Entity equality and hash are consistent."""
    # Create two entities with same properties
    entity1 = iottwinmaker.Entity(
        "Entity1",
        EntityName=entity_name1,
        WorkspaceId=workspace_id
    )
    
    entity2 = iottwinmaker.Entity(
        "Entity1",  # Same title
        EntityName=entity_name1,  # Same properties
        WorkspaceId=workspace_id
    )
    
    entity3 = iottwinmaker.Entity(
        "Entity2",  # Different title
        EntityName=entity_name1,
        WorkspaceId=workspace_id
    )
    
    entity4 = iottwinmaker.Entity(
        "Entity1",
        EntityName=entity_name2,  # Different property
        WorkspaceId=workspace_id
    )
    
    # Test equality
    assert entity1 == entity2, "Entities with same title and properties should be equal"
    assert entity1 != entity3, "Entities with different titles should not be equal"
    if entity_name1 != entity_name2:
        assert entity1 != entity4, "Entities with different properties should not be equal"
    
    # Test hash consistency
    if entity1 == entity2:
        assert hash(entity1) == hash(entity2), "Equal objects should have equal hashes"


# Test 8: Test PropertyDefinition with DataType
@given(
    is_external_id=st.booleans(),
    is_required=st.booleans(),
    is_time_series=st.booleans(),
    type_str=st.sampled_from(["STRING", "DOUBLE", "BOOLEAN", "INTEGER"])
)
def test_property_definition_with_datatype(is_external_id, is_required, is_time_series, type_str):
    """Test PropertyDefinition with DataType configuration."""
    data_type = iottwinmaker.DataType(Type=type_str)
    
    prop_def = iottwinmaker.PropertyDefinition(
        IsExternalId=is_external_id,
        IsRequiredInEntity=is_required,
        IsTimeSeries=is_time_series,
        DataType=data_type
    )
    
    prop_dict = prop_def.to_dict(validation=False)
    
    # Verify boolean properties are preserved correctly
    assert prop_dict["IsExternalId"] == is_external_id
    assert prop_dict["IsRequiredInEntity"] == is_required
    assert prop_dict["IsTimeSeries"] == is_time_series
    assert prop_dict["DataType"]["Type"] == type_str


# Test 9: Test Component with nested Status and Error
@given(
    component_name=valid_string,
    component_type_id=valid_string,
    error_code=valid_string,
    error_message=valid_string,
    state=st.sampled_from(["CREATING", "ACTIVE", "DELETING", "ERROR"])
)
def test_component_with_status_and_error(component_name, component_type_id, error_code, error_message, state):
    """Test Component with nested Status and Error objects."""
    error = iottwinmaker.Error(Code=error_code, Message=error_message)
    status = iottwinmaker.Status(Error=error, State=state)
    
    component = iottwinmaker.Component(
        ComponentName=component_name,
        ComponentTypeId=component_type_id,
        Status=status
    )
    
    comp_dict = component.to_dict(validation=False)
    
    # Verify nested structure is preserved
    assert comp_dict["ComponentName"] == component_name
    assert comp_dict["ComponentTypeId"] == component_type_id
    assert comp_dict["Status"]["State"] == state
    assert comp_dict["Status"]["Error"]["Code"] == error_code
    assert comp_dict["Status"]["Error"]["Message"] == error_message


# Test 10: Test SyncJob with all required properties
@given(
    sync_role=valid_string,
    sync_source=valid_string,
    workspace_id=valid_string
)
def test_syncjob_required_properties(sync_role, sync_source, workspace_id):
    """Test SyncJob with all required properties."""
    sync_job = iottwinmaker.SyncJob(
        "TestSyncJob",
        SyncRole=sync_role,
        SyncSource=sync_source,
        WorkspaceId=workspace_id
    )
    
    sync_dict = sync_job.to_dict(validation=False)
    
    # Verify all required properties are present
    props = sync_dict["Properties"]
    assert props["SyncRole"] == sync_role
    assert props["SyncSource"] == sync_source
    assert props["WorkspaceId"] == workspace_id
    
    # Verify Type is set correctly
    assert sync_dict["Type"] == "AWS::IoTTwinMaker::SyncJob"


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])