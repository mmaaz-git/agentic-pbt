"""Property-based tests for troposphere.shield module."""

import json
from hypothesis import given, strategies as st, assume, settings
from troposphere import shield
import pytest

# Increase number of test examples for thoroughness
test_settings = settings(max_examples=500)


# Strategies for generating valid AWS ARNs
def valid_arn():
    """Generate valid AWS ARNs."""
    services = ['ec2', 's3', 'lambda', 'iam', 'rds']
    regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-northeast-1']
    
    return st.builds(
        lambda service, region, account, resource: 
        f"arn:aws:{service}:{region}:{account}:{resource}",
        service=st.sampled_from(services),
        region=st.sampled_from(regions),
        account=st.text(alphabet='0123456789', min_size=12, max_size=12),
        resource=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-/', min_size=1, max_size=50)
    )


# Strategies for valid email addresses
def valid_email():
    """Generate valid email addresses."""
    return st.builds(
        lambda local, domain: f"{local}@{domain}.com",
        local=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789._-', min_size=1, max_size=20),
        domain=st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=1, max_size=20)
    )


# Strategies for valid phone numbers
def valid_phone():
    """Generate valid phone numbers."""
    return st.builds(
        lambda digits: f"+{digits}",
        digits=st.text(alphabet='0123456789', min_size=10, max_size=15)
    )


# Test 1: Round-trip property for EmergencyContact (AWSProperty)
@test_settings
@given(
    email=valid_email(),
    notes=st.text(min_size=0, max_size=100),
    phone=st.one_of(valid_phone(), st.none())
)
def test_emergency_contact_round_trip(email, notes, phone):
    """Test that EmergencyContact survives to_dict/from_dict round-trip."""
    kwargs = {'EmailAddress': email}
    if notes:
        kwargs['ContactNotes'] = notes
    if phone:
        kwargs['PhoneNumber'] = phone
    
    # Create original object
    original = shield.EmergencyContact(**kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    reconstructed = shield.EmergencyContact.from_dict(None, as_dict)
    
    # Check they produce the same dict representation
    assert reconstructed.to_dict() == as_dict


# Test 2: Round-trip property for DRTAccess (AWSObject)
@test_settings
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20),
    role_arn=valid_arn(),
    buckets=st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=3, max_size=63), min_size=0, max_size=5)
)
def test_drtaccess_round_trip(title, role_arn, buckets):
    """Test that DRTAccess survives to_dict/from_dict round-trip."""
    kwargs = {'RoleArn': role_arn}
    if buckets:
        kwargs['LogBucketList'] = buckets
    
    # Create original object
    original = shield.DRTAccess(title, **kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    # For AWSObject, we need to extract the Properties
    props = as_dict.get('Properties', {})
    reconstructed = shield.DRTAccess.from_dict(title, props)
    
    # Check they produce the same dict representation
    assert reconstructed.to_dict() == as_dict


# Test 3: Round-trip property for Protection (AWSObject)
@test_settings
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20),
    name=st.text(min_size=1, max_size=100),
    resource_arn=valid_arn(),
    health_check_arns=st.lists(valid_arn(), min_size=0, max_size=3)
)
def test_protection_round_trip(title, name, resource_arn, health_check_arns):
    """Test that Protection survives to_dict/from_dict round-trip."""
    kwargs = {'Name': name, 'ResourceArn': resource_arn}
    if health_check_arns:
        kwargs['HealthCheckArns'] = health_check_arns
    
    # Create original object
    original = shield.Protection(title, **kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    props = as_dict.get('Properties', {})
    reconstructed = shield.Protection.from_dict(title, props)
    
    # Check they produce the same dict representation
    assert reconstructed.to_dict() == as_dict


# Test 4: Title validation property
@test_settings
@given(title=st.text(min_size=1, max_size=50))
def test_title_validation(title):
    """Test that title validation correctly accepts/rejects titles."""
    # According to validate_title, titles must match ^[a-zA-Z0-9]+$
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    is_valid = bool(valid_names.match(title))
    
    if is_valid:
        # Should not raise an exception
        obj = shield.DRTAccess(title, RoleArn='arn:aws:iam::123456789012:role/Test')
        assert obj.title == title
    else:
        # Should raise ValueError
        with pytest.raises(ValueError, match='not alphanumeric'):
            shield.DRTAccess(title, RoleArn='arn:aws:iam::123456789012:role/Test')


# Test 5: Required field validation
@test_settings
@given(
    include_role=st.booleans(),
    include_email=st.booleans()
)
def test_required_field_validation(include_role, include_email):
    """Test that required fields are enforced."""
    # Test DRTAccess - RoleArn is required
    if include_role:
        drt = shield.DRTAccess('Test', RoleArn='arn:aws:iam::123456789012:role/Test')
        # Should succeed validation
        drt.to_dict()  # This triggers validation
    else:
        drt = shield.DRTAccess('Test')
        # Should fail validation
        with pytest.raises(ValueError, match='Resource RoleArn required'):
            drt.to_dict()
    
    # Test EmergencyContact - EmailAddress is required  
    if include_email:
        ec = shield.EmergencyContact(EmailAddress='test@example.com')
        ec.to_dict()  # Should succeed
    else:
        ec = shield.EmergencyContact()
        with pytest.raises(ValueError, match='Resource EmailAddress required'):
            ec.to_dict()


# Test 6: JSON serialization round-trip
@test_settings
@given(
    email=valid_email(),
    notes=st.text(min_size=0, max_size=50),
    phone=st.one_of(valid_phone(), st.none())
)
def test_json_round_trip(email, notes, phone):
    """Test that JSON serialization preserves object structure."""
    kwargs = {'EmailAddress': email}
    if notes:
        kwargs['ContactNotes'] = notes
    if phone:
        kwargs['PhoneNumber'] = phone
    
    # Create object and convert to JSON
    obj = shield.EmergencyContact(**kwargs)
    json_str = obj.to_json()
    
    # Parse JSON and compare to to_dict()
    parsed = json.loads(json_str)
    assert parsed == obj.to_dict()


# Test 7: ProactiveEngagement with nested EmergencyContact objects
@test_settings
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20),
    contacts=st.lists(
        st.builds(
            lambda email, notes: {'EmailAddress': email, 'ContactNotes': notes},
            email=valid_email(),
            notes=st.text(max_size=50)
        ),
        min_size=1,
        max_size=5
    ),
    status=st.sampled_from(['ENABLED', 'DISABLED'])
)
def test_proactive_engagement_nested_round_trip(title, contacts, status):
    """Test ProactiveEngagement with nested EmergencyContact objects."""
    # Create EmergencyContact objects
    contact_objs = [shield.EmergencyContact(**c) for c in contacts]
    
    # Create ProactiveEngagement
    pe = shield.ProactiveEngagement(
        title,
        EmergencyContactList=contact_objs,
        ProactiveEngagementStatus=status
    )
    
    # Test round-trip
    as_dict = pe.to_dict()
    props = as_dict.get('Properties', {})
    reconstructed = shield.ProactiveEngagement.from_dict(title, props)
    
    assert reconstructed.to_dict() == as_dict


# Test 8: ProtectionGroup round-trip
@test_settings
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20),
    aggregation=st.sampled_from(['SUM', 'MEAN', 'MAX']),
    pattern=st.sampled_from(['ALL', 'ARBITRARY', 'BY_RESOURCE_TYPE']),
    protection_group_id=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_', min_size=1, max_size=36),
    members=st.lists(valid_arn(), min_size=0, max_size=5),
    resource_type=st.one_of(st.none(), st.sampled_from(['ROUTE_53_HOSTED_ZONE', 'ELASTIC_IP_ALLOCATION', 'CLOUDFRONT_DISTRIBUTION']))
)
def test_protection_group_round_trip(title, aggregation, pattern, protection_group_id, members, resource_type):
    """Test ProtectionGroup round-trip property."""
    kwargs = {
        'Aggregation': aggregation,
        'Pattern': pattern,
        'ProtectionGroupId': protection_group_id
    }
    
    if members:
        kwargs['Members'] = members
    if resource_type:
        kwargs['ResourceType'] = resource_type
    
    # Create original object
    original = shield.ProtectionGroup(title, **kwargs)
    
    # Convert to dict and back
    as_dict = original.to_dict()
    props = as_dict.get('Properties', {})
    reconstructed = shield.ProtectionGroup.from_dict(title, props)
    
    # Check they produce the same dict representation
    assert reconstructed.to_dict() == as_dict


# Test 9: Action and ApplicationLayerAutomaticResponseConfiguration
@test_settings
@given(
    has_block=st.booleans(),
    has_count=st.booleans(),
    status=st.sampled_from(['ENABLED', 'DISABLED'])
)
def test_application_layer_config(has_block, has_count, status):
    """Test ApplicationLayerAutomaticResponseConfiguration with Action."""
    assume(has_block or has_count)  # At least one action type
    
    # Create Action
    action_kwargs = {}
    if has_block:
        action_kwargs['Block'] = {}
    if has_count:
        action_kwargs['Count'] = {}
    
    action = shield.Action(**action_kwargs)
    
    # Create ApplicationLayerAutomaticResponseConfiguration
    config = shield.ApplicationLayerAutomaticResponseConfiguration(
        Action=action,
        Status=status
    )
    
    # Test round-trip
    as_dict = config.to_dict()
    reconstructed = shield.ApplicationLayerAutomaticResponseConfiguration.from_dict(None, as_dict)
    
    assert reconstructed.to_dict() == as_dict