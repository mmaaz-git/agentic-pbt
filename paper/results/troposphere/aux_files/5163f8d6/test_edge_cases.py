"""Additional edge case tests for troposphere.shield."""

from troposphere import shield, Ref
import json


def test_aws_helper_function():
    """Test that AWSHelperFn objects work in shield resources."""
    # Create a Protection with a Ref for the Name
    p = shield.Protection(
        'MyProtection',
        Name=Ref('ProtectionName'),
        ResourceArn='arn:aws:ec2:us-west-2:123456789012:instance/i-123'
    )
    
    # Should be able to convert to dict without validation errors
    result = p.to_dict()
    assert result['Properties']['Name'] == {'Ref': 'ProtectionName'}


def test_equality_methods():
    """Test the equality methods for shield objects."""
    # Create two identical EmergencyContacts
    ec1 = shield.EmergencyContact(
        EmailAddress='test@example.com',
        ContactNotes='Test'
    )
    ec2 = shield.EmergencyContact(
        EmailAddress='test@example.com',
        ContactNotes='Test'
    )
    
    # They should be equal
    assert ec1 == ec2
    assert not (ec1 != ec2)
    
    # Different objects should not be equal
    ec3 = shield.EmergencyContact(
        EmailAddress='different@example.com',
        ContactNotes='Test'
    )
    assert ec1 != ec3
    assert not (ec1 == ec3)
    
    # Test AWSObject equality
    drt1 = shield.DRTAccess('Test1', RoleArn='arn:aws:iam::123456789012:role/Test')
    drt2 = shield.DRTAccess('Test1', RoleArn='arn:aws:iam::123456789012:role/Test')
    drt3 = shield.DRTAccess('Test2', RoleArn='arn:aws:iam::123456789012:role/Test')
    
    assert drt1 == drt2
    assert drt1 != drt3


def test_custom_attributes():
    """Test setting and getting custom attributes."""
    p = shield.Protection(
        'MyProtection',
        Name='Test',
        ResourceArn='arn:aws:ec2:us-west-2:123456789012:instance/i-123',
        DependsOn=['OtherResource'],
        Metadata={'key': 'value'}
    )
    
    # Check that attributes are properly set
    assert p.DependsOn == ['OtherResource']
    assert p.Metadata == {'key': 'value'}
    
    # Check that they appear in to_dict
    result = p.to_dict()
    assert 'DependsOn' in result
    assert 'Metadata' in result


def test_empty_properties():
    """Test objects with only required properties."""
    # EmergencyContact with only required field
    ec = shield.EmergencyContact(EmailAddress='test@example.com')
    result = ec.to_dict()
    assert result == {'EmailAddress': 'test@example.com'}
    
    # DRTAccess with only required field
    drt = shield.DRTAccess('Test', RoleArn='arn:aws:iam::123456789012:role/Test')
    result = drt.to_dict()
    assert result['Properties'] == {'RoleArn': 'arn:aws:iam::123456789012:role/Test'}


def test_complex_nested_structure():
    """Test complex nested structure with Protection containing ApplicationLayerAutomaticResponseConfiguration."""
    # Create nested structure
    action = shield.Action(Block={}, Count={})
    config = shield.ApplicationLayerAutomaticResponseConfiguration(
        Action=action,
        Status='ENABLED'
    )
    
    protection = shield.Protection(
        'MyProtection',
        Name='ComplexProtection',
        ResourceArn='arn:aws:ec2:us-west-2:123456789012:instance/i-123',
        ApplicationLayerAutomaticResponseConfiguration=config,
        HealthCheckArns=['arn:aws:route53:::healthcheck/abc123']
    )
    
    # Convert to dict
    result = protection.to_dict()
    
    # Check structure
    props = result['Properties']
    assert 'ApplicationLayerAutomaticResponseConfiguration' in props
    alc = props['ApplicationLayerAutomaticResponseConfiguration']
    assert alc['Status'] == 'ENABLED'
    assert 'Action' in alc
    assert 'Block' in alc['Action']
    assert 'Count' in alc['Action']
    
    # Test round-trip
    reconstructed = shield.Protection.from_dict('MyProtection', props)
    assert reconstructed.to_dict() == result


if __name__ == '__main__':
    test_aws_helper_function()
    test_equality_methods()
    test_custom_attributes()
    test_empty_properties()
    test_complex_nested_structure()
    print("All edge case tests passed!")