import troposphere.sso as sso
from hypothesis import given, strategies as st, assume, settings
import string


# Strategy for valid CloudFormation titles (alphanumeric only)
valid_title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=255
).filter(lambda s: s.isalnum())

# Strategy for arbitrary strings (including with special chars)
arbitrary_string_strategy = st.text(min_size=0, max_size=255)

# Strategy for ARN-like strings
arn_strategy = st.text(alphabet=string.ascii_letters + string.digits + ':/-', min_size=1, max_size=255)


@given(
    title=valid_title_strategy,
    app_provider_arn=arbitrary_string_strategy,
    instance_arn=arbitrary_string_strategy,
    name=arbitrary_string_strategy,
    description=st.one_of(st.none(), arbitrary_string_strategy),
    status=st.one_of(st.none(), arbitrary_string_strategy)
)
def test_application_round_trip(title, app_provider_arn, instance_arn, name, description, status):
    """Test that Application objects can round-trip through to_dict/from_dict"""
    
    # Create application with various properties
    kwargs = {
        'ApplicationProviderArn': app_provider_arn,
        'InstanceArn': instance_arn, 
        'Name': name
    }
    if description is not None:
        kwargs['Description'] = description
    if status is not None:
        kwargs['Status'] = status
    
    app1 = sso.Application(title, **kwargs)
    
    # Convert to dict and back
    dict_repr = app1.to_dict()
    app2 = sso.Application.from_dict(title, dict_repr['Properties'])
    
    # Properties should match
    assert app1.properties == app2.properties
    assert app1.title == app2.title
    

@given(
    title=valid_title_strategy,
    origin=arbitrary_string_strategy,
    app_url=st.one_of(st.none(), arbitrary_string_strategy),
    visibility=st.one_of(st.none(), arbitrary_string_strategy)
)
def test_nested_properties_round_trip(title, origin, app_url, visibility):
    """Test that nested properties are preserved through serialization"""
    
    # Create nested properties
    sign_in_kwargs = {'Origin': origin}
    if app_url is not None:
        sign_in_kwargs['ApplicationUrl'] = app_url
        
    sign_in = sso.SignInOptions(**sign_in_kwargs)
    
    portal_kwargs = {'SignInOptions': sign_in}
    if visibility is not None:
        portal_kwargs['Visibility'] = visibility
        
    portal = sso.PortalOptionsConfiguration(**portal_kwargs)
    
    app1 = sso.Application(
        title,
        ApplicationProviderArn='test_arn',
        InstanceArn='test_instance',
        Name='test_name',
        PortalOptions=portal
    )
    
    # Round-trip through dict
    dict_repr = app1.to_dict()
    app2 = sso.Application.from_dict(title, dict_repr['Properties'])
    
    # Nested properties should be preserved
    assert app1.properties == app2.properties
    

@given(title=arbitrary_string_strategy)  
def test_title_validation_consistency(title):
    """Test that title validation is consistent"""
    
    # Skip empty titles as they're always invalid
    assume(len(title) > 0)
    
    app = sso.Application(title, Name='test')
    
    # Check if validate_title accepts or rejects this title
    try:
        app.validate_title()
        is_valid = True
    except ValueError:
        is_valid = False
    
    # The title should be valid if and only if it's alphanumeric
    expected_valid = title.isalnum()
    
    assert is_valid == expected_valid, f"Title {repr(title)} validation inconsistent: got {is_valid}, expected {expected_valid}"


@given(
    title=valid_title_strategy,
    permission_set_arn=arbitrary_string_strategy,
    instance_arn=arbitrary_string_strategy,
    principal_id=arbitrary_string_strategy,
    principal_type=arbitrary_string_strategy,
    target_id=arbitrary_string_strategy,
    target_type=arbitrary_string_strategy
)
def test_assignment_round_trip(title, permission_set_arn, instance_arn, 
                               principal_id, principal_type, target_id, target_type):
    """Test Assignment class round-trip property"""
    
    assignment1 = sso.Assignment(
        title,
        PermissionSetArn=permission_set_arn,
        InstanceArn=instance_arn,
        PrincipalId=principal_id,
        PrincipalType=principal_type,
        TargetId=target_id,
        TargetType=target_type
    )
    
    dict_repr = assignment1.to_dict()
    assignment2 = sso.Assignment.from_dict(title, dict_repr['Properties'])
    
    assert assignment1.properties == assignment2.properties
    assert assignment1.title == assignment2.title


@given(
    title=valid_title_strategy,
    key=arbitrary_string_strategy,
    sources=st.lists(arbitrary_string_strategy, min_size=1, max_size=10)
)
def test_access_control_attribute_round_trip(title, key, sources):
    """Test AccessControlAttribute nested property round-trip"""
    
    # Create nested AccessControlAttribute
    attr_value = sso.AccessControlAttributeValue(Source=sources)
    attr = sso.AccessControlAttribute(Key=key, Value=attr_value)
    
    config = sso.InstanceAccessControlAttributeConfiguration(
        title,
        InstanceArn='test_arn',
        AccessControlAttributes=[attr]
    )
    
    dict_repr = config.to_dict()
    config2 = sso.InstanceAccessControlAttributeConfiguration.from_dict(
        title, dict_repr['Properties']
    )
    
    assert config.properties == config2.properties


@given(
    title=valid_title_strategy,
    name=arbitrary_string_strategy,
    path=st.one_of(st.none(), arbitrary_string_strategy),
    managed_policy_arn=st.one_of(st.none(), arbitrary_string_strategy)
)  
def test_permission_set_boundaries(title, name, path, managed_policy_arn):
    """Test PermissionSet with PermissionsBoundary"""
    
    # Create CustomerManagedPolicyReference
    policy_ref_kwargs = {'Name': name}
    if path is not None:
        policy_ref_kwargs['Path'] = path
    policy_ref = sso.CustomerManagedPolicyReference(**policy_ref_kwargs)
    
    # Create PermissionsBoundary
    boundary_kwargs = {}
    if managed_policy_arn is not None:
        boundary_kwargs['ManagedPolicyArn'] = managed_policy_arn
    boundary_kwargs['CustomerManagedPolicyReference'] = policy_ref
    boundary = sso.PermissionsBoundary(**boundary_kwargs)
    
    # Create PermissionSet with boundary
    perm_set = sso.PermissionSet(
        title,
        InstanceArn='test_arn',
        Name='test_name',
        PermissionsBoundary=boundary
    )
    
    dict_repr = perm_set.to_dict()
    perm_set2 = sso.PermissionSet.from_dict(title, dict_repr['Properties'])
    
    assert perm_set.properties == perm_set2.properties