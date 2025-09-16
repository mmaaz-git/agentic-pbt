"""Property-based tests for troposphere.identitystore module."""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the troposphere environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.identitystore import Group, GroupMembership, MemberId


# Strategy for valid CloudFormation resource titles (must be alphanumeric)
valid_title = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=255)

# Strategy for ID-like strings (typical AWS resource IDs)
resource_id = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"), min_size=1, max_size=100)

# Strategy for descriptions
description = st.text(min_size=0, max_size=500)


@given(
    title=valid_title,
    display_name=st.text(min_size=1, max_size=100),
    identity_store_id=resource_id,
    description=st.one_of(st.none(), description)
)
def test_group_creation_and_serialization(title, display_name, identity_store_id, description):
    """Test that Group objects can be created and serialized properly."""
    # Create a Group object
    kwargs = {
        'DisplayName': display_name,
        'IdentityStoreId': identity_store_id
    }
    if description is not None:
        kwargs['Description'] = description
    
    group = Group(title=title, **kwargs)
    
    # Test that properties are set correctly
    assert group.DisplayName == display_name
    assert group.IdentityStoreId == identity_store_id
    if description is not None:
        assert group.Description == description
    
    # Test serialization to dict
    group_dict = group.to_dict()
    assert 'Type' in group_dict
    assert group_dict['Type'] == 'AWS::IdentityStore::Group'
    assert 'Properties' in group_dict
    assert group_dict['Properties']['DisplayName'] == display_name
    assert group_dict['Properties']['IdentityStoreId'] == identity_store_id
    
    # Test JSON serialization round-trip
    json_str = group.to_json()
    parsed = json.loads(json_str)
    assert parsed == group_dict


@given(
    title=valid_title,
    group_id=resource_id,
    identity_store_id=resource_id,
    user_id=resource_id
)
def test_group_membership_creation_and_validation(title, group_id, identity_store_id, user_id):
    """Test GroupMembership creation with nested MemberId property."""
    # Create MemberId object
    member_id = MemberId(UserId=user_id)
    
    # Create GroupMembership with MemberId object
    membership = GroupMembership(
        title=title,
        GroupId=group_id,
        IdentityStoreId=identity_store_id,
        MemberId=member_id
    )
    
    # Verify properties
    assert membership.GroupId == group_id
    assert membership.IdentityStoreId == identity_store_id
    assert membership.MemberId == member_id
    
    # Test serialization
    membership_dict = membership.to_dict()
    assert membership_dict['Type'] == 'AWS::IdentityStore::GroupMembership'
    assert membership_dict['Properties']['GroupId'] == group_id
    assert membership_dict['Properties']['IdentityStoreId'] == identity_store_id
    assert 'MemberId' in membership_dict['Properties']
    assert membership_dict['Properties']['MemberId']['UserId'] == user_id


@given(title=valid_title)
def test_required_properties_validation(title):
    """Test that missing required properties raise appropriate errors."""
    # Test Group without required properties
    with pytest.raises(ValueError, match="Resource DisplayName required"):
        Group(title=title).to_dict()
    
    # Test Group with only DisplayName (missing IdentityStoreId)
    with pytest.raises(ValueError, match="Resource IdentityStoreId required"):
        Group(title=title, DisplayName="TestGroup").to_dict()
    
    # Test GroupMembership without required properties
    with pytest.raises(ValueError, match="Resource GroupId required"):
        GroupMembership(title=title).to_dict()


@given(
    invalid_title=st.text(min_size=1).filter(lambda s: not s.replace('_', '').isalnum() or '_' in s or ' ' in s or '-' in s)
)
def test_invalid_title_validation(invalid_title):
    """Test that invalid titles (non-alphanumeric) are rejected."""
    assume(invalid_title != "")  # Empty string is a different case
    
    with pytest.raises(ValueError, match="not alphanumeric"):
        Group(
            title=invalid_title,
            DisplayName="TestDisplay",
            IdentityStoreId="store-123"
        )


@given(
    title=valid_title,
    display_name=st.text(min_size=1, max_size=100),
    identity_store_id=resource_id,
    invalid_value=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_type_validation_for_string_properties(title, display_name, identity_store_id, invalid_value):
    """Test that setting non-string values for string properties raises errors."""
    # Test setting DisplayName to non-string
    with pytest.raises(TypeError):
        Group(
            title=title,
            DisplayName=invalid_value,
            IdentityStoreId=identity_store_id
        )
    
    # Test setting IdentityStoreId to non-string
    with pytest.raises(TypeError):
        Group(
            title=title,
            DisplayName=display_name,
            IdentityStoreId=invalid_value
        )


@given(
    title1=valid_title,
    title2=valid_title,
    display_name=st.text(min_size=1, max_size=100),
    identity_store_id=resource_id
)
def test_equality_property(title1, title2, display_name, identity_store_id):
    """Test equality: objects with same properties should be equal (ignoring title)."""
    group1 = Group(
        title=title1,
        DisplayName=display_name,
        IdentityStoreId=identity_store_id
    )
    
    group2 = Group(
        title=title1,  # Same title
        DisplayName=display_name,
        IdentityStoreId=identity_store_id
    )
    
    group3 = Group(
        title=title2,  # Different title
        DisplayName=display_name,
        IdentityStoreId=identity_store_id
    )
    
    # Groups with same title and properties should be equal
    assert group1 == group2
    
    # Groups with different titles are not equal (title is part of equality)
    if title1 != title2:
        assert group1 != group3


@given(user_id=resource_id)
def test_member_id_property_serialization(user_id):
    """Test MemberId property class serialization."""
    member = MemberId(UserId=user_id)
    
    # Test that it has the UserId property
    assert member.UserId == user_id
    
    # Test serialization
    member_dict = member.to_dict()
    assert member_dict['UserId'] == user_id
    
    # MemberId is an AWSProperty, so it shouldn't have a Type field
    assert 'Type' not in member_dict


@given(
    title=valid_title,
    display_name=st.text(min_size=1, max_size=100),
    identity_store_id=resource_id
)
@settings(max_examples=100)
def test_no_validation_mode(title, display_name, identity_store_id):
    """Test that no_validation() disables validation checks."""
    # Create a Group without required properties but with no_validation
    group = Group(title=title).no_validation()
    
    # This should not raise an error even though required properties are missing
    group_dict = group.to_dict()
    
    # The dict should still have the Type but Properties might be empty
    assert 'Type' in group_dict or group_dict == {}  # May return empty dict without properties


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])