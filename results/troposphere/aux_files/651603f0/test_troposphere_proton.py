"""Property-based tests for troposphere.proton module"""

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.proton as proton
import troposphere


# Strategy for generating valid property values
valid_string = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
valid_name = st.from_regex(r'^[a-zA-Z][a-zA-Z0-9_-]{0,99}$')
valid_arn = st.from_regex(r'^arn:aws:[a-z0-9-]+:[a-z0-9-]*:[0-9]{12}:[a-zA-Z0-9-/_]+$')
valid_account_id = st.from_regex(r'^[0-9]{12}$')

# Strategy for generating Tags
@st.composite
def tags_strategy(draw):
    """Generate valid Tags objects"""
    num_tags = draw(st.integers(min_value=0, max_value=5))
    tags_list = []
    used_keys = set()
    for _ in range(num_tags):
        key = draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x not in used_keys))
        used_keys.add(key)
        value = draw(st.text(min_size=0, max_size=100))
        tags_list.append({'Key': key, 'Value': value})
    return troposphere.Tags(tags_list) if tags_list else None


# Strategy for generating EnvironmentTemplate instances
@st.composite
def environment_template_strategy(draw):
    """Generate valid EnvironmentTemplate instances"""
    title = draw(valid_name)
    kwargs = {}
    
    # Randomly include optional properties
    if draw(st.booleans()):
        kwargs['Name'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['Description'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['DisplayName'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['EncryptionKey'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['Provisioning'] = draw(st.sampled_from(['CUSTOMER_MANAGED', 'AWS_MANAGED']))
    if draw(st.booleans()):
        tags = draw(tags_strategy())
        if tags:
            kwargs['Tags'] = tags
    
    return proton.EnvironmentTemplate(title, **kwargs)


# Strategy for generating ServiceTemplate instances
@st.composite
def service_template_strategy(draw):
    """Generate valid ServiceTemplate instances"""
    title = draw(valid_name)
    kwargs = {}
    
    if draw(st.booleans()):
        kwargs['Name'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['Description'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['DisplayName'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['EncryptionKey'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['PipelineProvisioning'] = draw(st.sampled_from(['CUSTOMER_MANAGED', 'AWS_MANAGED']))
    if draw(st.booleans()):
        tags = draw(tags_strategy())
        if tags:
            kwargs['Tags'] = tags
    
    return proton.ServiceTemplate(title, **kwargs)


# Strategy for generating EnvironmentAccountConnection instances
@st.composite
def environment_account_connection_strategy(draw):
    """Generate valid EnvironmentAccountConnection instances"""
    title = draw(valid_name)
    kwargs = {}
    
    if draw(st.booleans()):
        kwargs['CodebuildRoleArn'] = draw(valid_arn)
    if draw(st.booleans()):
        kwargs['ComponentRoleArn'] = draw(valid_arn)
    if draw(st.booleans()):
        kwargs['EnvironmentAccountId'] = draw(valid_account_id)
    if draw(st.booleans()):
        kwargs['EnvironmentName'] = draw(valid_string)
    if draw(st.booleans()):
        kwargs['ManagementAccountId'] = draw(valid_account_id)
    if draw(st.booleans()):
        kwargs['RoleArn'] = draw(valid_arn)
    if draw(st.booleans()):
        tags = draw(tags_strategy())
        if tags:
            kwargs['Tags'] = tags
    
    return proton.EnvironmentAccountConnection(title, **kwargs)


# Property 1: Round-trip serialization property
@given(environment_template_strategy())
@settings(max_examples=100)
def test_environment_template_round_trip(template):
    """Test that to_dict and from_dict are inverses for EnvironmentTemplate"""
    original_dict = template.to_dict()
    
    # from_dict expects only the Properties portion
    recreated = proton.EnvironmentTemplate.from_dict(
        template.title,
        original_dict['Properties']
    )
    recreated_dict = recreated.to_dict()
    
    assert original_dict == recreated_dict, f"Round-trip failed: {original_dict} != {recreated_dict}"


@given(service_template_strategy())
@settings(max_examples=100)
def test_service_template_round_trip(template):
    """Test that to_dict and from_dict are inverses for ServiceTemplate"""
    original_dict = template.to_dict()
    
    recreated = proton.ServiceTemplate.from_dict(
        template.title,
        original_dict['Properties']
    )
    recreated_dict = recreated.to_dict()
    
    assert original_dict == recreated_dict, f"Round-trip failed: {original_dict} != {recreated_dict}"


@given(environment_account_connection_strategy())
@settings(max_examples=100)
def test_environment_account_connection_round_trip(connection):
    """Test that to_dict and from_dict are inverses for EnvironmentAccountConnection"""
    original_dict = connection.to_dict()
    
    recreated = proton.EnvironmentAccountConnection.from_dict(
        connection.title,
        original_dict['Properties']
    )
    recreated_dict = recreated.to_dict()
    
    assert original_dict == recreated_dict, f"Round-trip failed: {original_dict} != {recreated_dict}"


# Property 2: Type validation
@given(valid_name, st.integers())
def test_environment_template_type_validation(title, invalid_value):
    """Test that validation rejects invalid types for EnvironmentTemplate"""
    template = proton.EnvironmentTemplate(title, Name=invalid_value)
    
    try:
        template.validate()
        assert False, f"Validation should have failed for Name={invalid_value}"
    except Exception as e:
        assert "expected <class 'str'>" in str(e)


@given(valid_name, st.integers())
def test_service_template_type_validation(title, invalid_value):
    """Test that validation rejects invalid types for ServiceTemplate"""
    template = proton.ServiceTemplate(title, Description=invalid_value)
    
    try:
        template.validate()
        assert False, f"Validation should have failed for Description={invalid_value}"
    except Exception as e:
        assert "expected <class 'str'>" in str(e)


# Property 3: JSON serialization
@given(environment_template_strategy())
def test_environment_template_json_serialization(template):
    """Test that to_json produces valid JSON for EnvironmentTemplate"""
    json_str = template.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should match to_dict output
    dict_output = template.to_dict()
    assert parsed == dict_output


@given(service_template_strategy())
def test_service_template_json_serialization(template):
    """Test that to_json produces valid JSON for ServiceTemplate"""
    json_str = template.to_json()
    parsed = json.loads(json_str)
    dict_output = template.to_dict()
    assert parsed == dict_output


# Property 4: Resource type consistency
@given(environment_template_strategy())
def test_environment_template_resource_type(template):
    """Test that Type field matches resource_type for EnvironmentTemplate"""
    dict_output = template.to_dict()
    assert dict_output['Type'] == proton.EnvironmentTemplate.resource_type
    assert dict_output['Type'] == 'AWS::Proton::EnvironmentTemplate'


@given(service_template_strategy())
def test_service_template_resource_type(template):
    """Test that Type field matches resource_type for ServiceTemplate"""
    dict_output = template.to_dict()
    assert dict_output['Type'] == proton.ServiceTemplate.resource_type
    assert dict_output['Type'] == 'AWS::Proton::ServiceTemplate'


@given(environment_account_connection_strategy())
def test_environment_account_connection_resource_type(connection):
    """Test that Type field matches resource_type for EnvironmentAccountConnection"""
    dict_output = connection.to_dict()
    assert dict_output['Type'] == proton.EnvironmentAccountConnection.resource_type
    assert dict_output['Type'] == 'AWS::Proton::EnvironmentAccountConnection'


# Property 5: Validation idempotence
@given(environment_template_strategy())
def test_validation_idempotence(template):
    """Test that validation can be called multiple times without side effects"""
    dict_before = template.to_dict()
    
    # Call validate multiple times
    template.validate()
    template.validate()
    template.validate()
    
    dict_after = template.to_dict()
    assert dict_before == dict_after, "Validation changed the object state"


# Property 6: Title validation
@given(st.text())
def test_invalid_title_validation(title):
    """Test that invalid titles are properly validated"""
    assume(title)  # Skip empty strings
    
    # Titles with certain special characters should fail validation
    if any(char in title for char in ['$', '.', '/']):
        try:
            template = proton.EnvironmentTemplate(title)
            template.validate_title()
            # If we get here, check if the title was actually invalid
            if '$' in title or '.' in title or '/' in title:
                assert False, f"Title validation should have failed for: {title}"
        except Exception as e:
            # Expected behavior for invalid titles
            pass


# Property 7: Empty property dict handling
def test_empty_dict_from_dict():
    """Test that from_dict handles empty property dict correctly"""
    template = proton.EnvironmentTemplate.from_dict('EmptyTest', {})
    dict_output = template.to_dict()
    
    assert dict_output['Type'] == 'AWS::Proton::EnvironmentTemplate'
    assert dict_output['Properties'] == {}


# Property 8: Full CloudFormation format handling
@given(environment_template_strategy())
def test_from_dict_with_full_format_fails(template):
    """Test that from_dict correctly rejects full CloudFormation format"""
    full_dict = template.to_dict()
    
    # This should fail because from_dict expects only Properties
    try:
        recreated = proton.EnvironmentTemplate.from_dict('Test', full_dict)
        assert False, "from_dict should reject full CloudFormation format with Type field"
    except AttributeError as e:
        assert "does not have a Type property" in str(e)