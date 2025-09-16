"""Property-based tests for troposphere.route53profiles module."""

import json
from hypothesis import given, strategies as st, assume
import troposphere
import troposphere.route53profiles as r53p


# Strategy for valid names (non-empty strings)
valid_name = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

# Strategy for valid IDs
valid_id = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

# Strategy for valid ARNs (simplified)
valid_arn = st.text(min_size=1, max_size=200).filter(lambda x: x.strip())


@given(name=valid_name)
def test_profile_json_roundtrip(name):
    """Test that Profile can round-trip through JSON serialization."""
    # Create a profile with required Name property
    profile = r53p.Profile('TestProfile', Name=name)
    
    # Convert to JSON and back
    json_str = profile.to_json()
    parsed = json.loads(json_str)
    
    # Attempt to recreate from parsed dict
    # This should work if from_dict is the inverse of to_json
    recreated = r53p.Profile.from_dict('Recreated', parsed)
    
    # The recreated object should produce the same JSON
    assert recreated.to_json() == json_str


@given(name=valid_name, profile_id=valid_id, resource_id=valid_id)
def test_profile_association_json_roundtrip(name, profile_id, resource_id):
    """Test that ProfileAssociation can round-trip through JSON."""
    # Create association with all required properties
    assoc = r53p.ProfileAssociation(
        'TestAssoc',
        Name=name,
        ProfileId=profile_id,
        ResourceId=resource_id
    )
    
    # Convert to JSON and back
    json_str = assoc.to_json()
    parsed = json.loads(json_str)
    
    # Attempt to recreate from parsed dict
    recreated = r53p.ProfileAssociation.from_dict('Recreated', parsed)
    
    # The recreated object should produce the same JSON
    assert recreated.to_json() == json_str


@given(name=valid_name)
def test_profile_validate_to_dict_consistency(name):
    """Test that validate() and to_dict() are consistent about validation."""
    # Create a valid profile
    profile = r53p.Profile('Test', Name=name)
    
    # validate() should succeed (return None or not raise)
    validation_result = profile.validate()
    
    # to_dict() should also succeed
    dict_result = profile.to_dict()
    
    # Both should succeed for valid input
    assert validation_result is None  # validate returns None on success
    assert dict_result is not None
    
    # Test invalid profile
    invalid_profile = r53p.Profile('Invalid')
    
    # If validate() returns None (success), to_dict() should also succeed
    invalid_validation = invalid_profile.validate()
    if invalid_validation is None:
        # validate() says it's valid, so to_dict() should work
        invalid_dict = invalid_profile.to_dict()
        assert invalid_dict is not None


@given(name=valid_name)
def test_profile_property_get_set_consistency(name):
    """Test that setting and getting properties is consistent."""
    profile = r53p.Profile('Test')
    
    # Set the Name property
    profile.Name = name
    
    # Getting it back should return the same value
    assert profile.Name == name
    
    # It should also be in the properties dict
    assert profile.properties['Name'] == name
    
    # Setting again should update
    new_name = name + "_modified"
    profile.Name = new_name
    assert profile.Name == new_name
    assert profile.properties['Name'] == new_name


@given(
    name=valid_name,
    profile_id=valid_id, 
    resource_id=valid_id,
    arn=valid_arn
)
def test_profile_association_property_consistency(name, profile_id, resource_id, arn):
    """Test ProfileAssociation property get/set consistency."""
    assoc = r53p.ProfileAssociation('Test')
    
    # Set all required properties
    assoc.Name = name
    assoc.ProfileId = profile_id
    assoc.ResourceId = resource_id
    
    # Optional property
    assoc.Arn = arn
    
    # All should be retrievable
    assert assoc.Name == name
    assert assoc.ProfileId == profile_id
    assert assoc.ResourceId == resource_id
    assert assoc.Arn == arn
    
    # All should be in properties dict
    assert assoc.properties['Name'] == name
    assert assoc.properties['ProfileId'] == profile_id
    assert assoc.properties['ResourceId'] == resource_id
    assert assoc.properties['Arn'] == arn


@given(tag_dict=st.dictionaries(
    keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    values=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    min_size=1,
    max_size=10
))
def test_tags_json_serialization(tag_dict):
    """Test that Tags serialize correctly in JSON output."""
    profile = r53p.Profile('Test', Name='TestProfile')
    
    # Create and set Tags
    tags = troposphere.Tags(tag_dict)
    profile.Tags = tags
    
    # Convert to JSON
    json_str = profile.to_json()
    parsed = json.loads(json_str)
    
    # Tags should be serialized as a list of Key/Value pairs
    assert 'Tags' in parsed['Properties']
    tags_list = parsed['Properties']['Tags']
    
    # Check all tags are present
    assert len(tags_list) == len(tag_dict)
    
    # Verify each tag
    for tag_item in tags_list:
        assert 'Key' in tag_item
        assert 'Value' in tag_item
        assert tag_item['Value'] == tag_dict[tag_item['Key']]