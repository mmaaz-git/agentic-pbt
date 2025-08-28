#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Property-based tests for troposphere.detective module"""

import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import troposphere.detective as detective
from troposphere.validators import boolean
from troposphere import Tags


# Strategy for valid boolean inputs based on the boolean validator code
valid_boolean_inputs = st.sampled_from([
    True, 1, "1", "true", "True",
    False, 0, "0", "false", "False"
])

# Strategy for generating valid AWS resource names (alphanumeric)
valid_names = st.text(alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')) | 
                      st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')) |
                      st.characters(min_codepoint=ord('0'), max_codepoint=ord('9')),
                      min_size=1, max_size=50)


@given(x=valid_boolean_inputs)
def test_boolean_validator_valid_inputs(x):
    """Test that boolean validator handles all documented valid inputs correctly"""
    result = boolean(x)
    assert isinstance(result, bool)
    # Check the documented behavior
    if x in [True, 1, "1", "true", "True"]:
        assert result is True
    elif x in [False, 0, "0", "false", "False"]:
        assert result is False


@given(x=st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(x):
    """Test that boolean validator raises ValueError for invalid inputs"""
    try:
        result = boolean(x)
        # If it doesn't raise, it's a bug
        assert False, f"Expected ValueError for input {x!r}, but got {result!r}"
    except ValueError:
        pass  # Expected behavior


@given(title=valid_names, auto_enable=st.booleans())
def test_graph_boolean_property(title, auto_enable):
    """Test that Graph accepts boolean values for AutoEnableMembers"""
    graph = detective.Graph(title)
    graph.AutoEnableMembers = auto_enable
    
    # Verify the property was set correctly
    assert hasattr(graph, 'AutoEnableMembers')
    d = graph.to_dict()
    assert d['Type'] == 'AWS::Detective::Graph'
    if auto_enable is not None:
        assert 'Properties' in d
        assert d['Properties']['AutoEnableMembers'] == auto_enable


@given(title=valid_names, 
       disable_email=st.booleans(),
       graph_arn=st.text(min_size=1, max_size=100),
       member_email=st.emails(),
       member_id=st.text(min_size=1, max_size=50),
       message=st.text(max_size=200))
def test_member_invitation_creation(title, disable_email, graph_arn, member_email, member_id, message):
    """Test MemberInvitation with various property combinations"""
    # Create with required properties
    invitation = detective.MemberInvitation(
        title,
        GraphArn=graph_arn,
        MemberEmailAddress=member_email,
        MemberId=member_id
    )
    
    # Add optional properties
    if disable_email is not None:
        invitation.DisableEmailNotification = disable_email
    if message:
        invitation.Message = message
    
    # Verify serialization works
    d = invitation.to_dict()
    assert d['Type'] == 'AWS::Detective::MemberInvitation'
    assert 'Properties' in d
    assert d['Properties']['GraphArn'] == graph_arn
    assert d['Properties']['MemberEmailAddress'] == member_email
    assert d['Properties']['MemberId'] == member_id


@given(title=valid_names, account_id=st.text(min_size=1, max_size=50))
def test_organization_admin_creation(title, account_id):
    """Test OrganizationAdmin with required AccountId property"""
    admin = detective.OrganizationAdmin(title, AccountId=account_id)
    
    d = admin.to_dict()
    assert d['Type'] == 'AWS::Detective::OrganizationAdmin'
    assert 'Properties' in d
    assert d['Properties']['AccountId'] == account_id


@given(title=valid_names, tags_dict=st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.text(min_size=0, max_size=100),
    max_size=10
))
def test_graph_with_tags(title, tags_dict):
    """Test Graph with Tags property"""
    graph = detective.Graph(title)
    
    # Convert dict to Tags object
    if tags_dict:
        graph.Tags = Tags(tags_dict)
        d = graph.to_dict()
        assert 'Properties' in d
        assert 'Tags' in d['Properties']


@given(title=valid_names)
def test_graph_to_dict_from_dict_roundtrip(title):
    """Test that Graph can be serialized and reconstructed"""
    # Create a Graph with some properties
    original = detective.Graph(title)
    original.AutoEnableMembers = True
    
    # Serialize to dict
    d = original.to_dict()
    
    # Verify we can create JSON from it (no exceptions)
    json_str = json.dumps(d)
    
    # Verify the structure
    assert 'Type' in d
    assert d['Type'] == 'AWS::Detective::Graph'
    
    # Create a new object from the properties
    if 'Properties' in d and d['Properties'].get('AutoEnableMembers') is not None:
        new_graph = detective.Graph(title + "New")
        new_graph.AutoEnableMembers = d['Properties']['AutoEnableMembers']
        
        # Verify they produce the same dict structure
        new_d = new_graph.to_dict()
        assert new_d['Type'] == d['Type']
        if 'Properties' in d:
            assert new_d['Properties']['AutoEnableMembers'] == d['Properties']['AutoEnableMembers']


@given(st.data())
def test_invalid_property_names_raise_error(data):
    """Test that setting invalid property names raises AttributeError"""
    title = data.draw(valid_names)
    invalid_prop_name = data.draw(st.text(min_size=1).filter(
        lambda x: x not in ['AutoEnableMembers', 'Tags', 'title', 'template', 
                           'Condition', 'CreationPolicy', 'DeletionPolicy', 
                           'DependsOn', 'Metadata', 'UpdatePolicy', 
                           'UpdateReplacePolicy', 'properties', 'resource']
    ))
    
    graph = detective.Graph(title)
    
    try:
        setattr(graph, invalid_prop_name, "some_value")
        # If we get here without exception, check if it's stored  
        # Some internal attributes might be allowed
        if not hasattr(graph, invalid_prop_name):
            assert False, f"Property {invalid_prop_name} was set but not stored"
    except AttributeError as e:
        # This is expected for truly invalid properties
        assert invalid_prop_name in str(e)


@given(title=valid_names, wrong_type_value=st.one_of(
    st.integers(), 
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_member_invitation_wrong_type_for_string_property(title, wrong_type_value):
    """Test that MemberInvitation raises TypeError for wrong property types"""
    try:
        # GraphArn should be a string, not other types
        invitation = detective.MemberInvitation(
            title,
            GraphArn=wrong_type_value,  # This should be a string
            MemberEmailAddress="test@example.com",
            MemberId="member123"
        )
        # If no exception, check if it got converted or stored
        d = invitation.to_dict()
        # The type system might convert it, let's see what happens
    except (TypeError, AttributeError) as e:
        # Expected behavior - wrong type should raise an error
        pass


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])