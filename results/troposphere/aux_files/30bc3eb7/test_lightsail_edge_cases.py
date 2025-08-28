#!/usr/bin/env python3
"""Edge case property-based tests for troposphere.lightsail module"""

import sys
import json

# Add the environment packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import troposphere.lightsail as lightsail
from troposphere import Template

# Test required properties validation
def test_missing_required_properties():
    """Missing required properties should raise ValueError on to_dict()"""
    # Create Alarm without required properties
    alarm = lightsail.Alarm(title="TestAlarm")
    
    try:
        alarm.to_dict()
        assert False, "Should have raised ValueError for missing required properties"
    except ValueError as e:
        assert "required" in str(e).lower()

# Test boolean validator edge cases
def test_boolean_validator_edge_cases():
    """Test boolean validator with edge case values"""
    from troposphere.validators import boolean
    
    # Test valid values
    assert boolean(True) is True
    assert boolean(False) is False
    assert boolean(1) is True
    assert boolean(0) is False
    assert boolean("true") is True
    assert boolean("false") is False
    assert boolean("True") is True
    assert boolean("False") is False
    
    # Test invalid values should raise
    invalid_values = [2, -1, "yes", "no", "1", "0", None, [], {}]
    for val in invalid_values:
        try:
            boolean(val)
            if val not in ["1", "0"]:  # These are actually valid
                assert False, f"Should have raised for {val}"
        except ValueError:
            pass

# Test integer validator with string numbers
def test_integer_validator_string_numbers():
    """Integer validator should accept string representations"""
    from troposphere.validators import integer
    
    # Valid string integers
    assert integer("123") == "123"
    assert integer("-456") == "-456"
    assert integer("0") == "0"
    
    # Invalid strings should raise
    invalid = ["abc", "12.34", "1e10", "", None]
    for val in invalid:
        try:
            integer(val)
            assert False, f"Should have raised for {val}"
        except (ValueError, TypeError):
            pass

# Test property assignment with None
@given(
    name=st.text(min_size=1, max_size=50)
)
def test_none_property_assignment(name):
    """Assigning None to optional properties"""
    instance = lightsail.Instance(
        title="TestInstance",
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName=name
    )
    
    # Try setting optional property to None
    instance.KeyPairName = None
    instance.UserData = None
    
    # Should handle None appropriately
    result = instance.to_dict()
    props = result["Properties"]
    
    # None values might be included or excluded
    if "KeyPairName" in props:
        assert props["KeyPairName"] is None
    if "UserData" in props:
        assert props["UserData"] is None

# Test list properties with empty lists
def test_empty_list_properties():
    """List properties should accept empty lists"""
    cert = lightsail.Certificate(
        title="TestCert",
        CertificateName="mycert",
        DomainName="example.com"
    )
    
    cert.SubjectAlternativeNames = []
    assert cert.SubjectAlternativeNames == []
    
    lb = lightsail.LoadBalancer(
        title="TestLB",
        LoadBalancerName="mylb",
        InstancePort=80
    )
    
    lb.AttachedInstances = []
    assert lb.AttachedInstances == []

# Test very long strings
@given(
    long_string=st.text(min_size=1000, max_size=10000)
)
def test_long_string_properties(long_string):
    """Properties should handle very long strings"""
    instance = lightsail.Instance(
        title="TestInstance",
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName="test"
    )
    
    # UserData can be quite long
    instance.UserData = long_string
    assert instance.UserData == long_string
    
    # Should serialize properly
    result = instance.to_dict()
    assert result["Properties"]["UserData"] == long_string

# Test special characters in strings
@given(
    special_chars=st.text(alphabet="!@#$%^&*()_+-=[]{}|;:'\",.<>?/\\`~")
)
def test_special_characters_in_strings(special_chars):
    """String properties should handle special characters"""
    assume(len(special_chars) > 0)
    
    # Some properties might accept special characters
    param = lightsail.RelationalDatabaseParameter()
    param.ParameterValue = special_chars
    param.Description = special_chars
    
    assert param.ParameterValue == special_chars
    assert param.Description == special_chars

# Test numeric boundaries
def test_numeric_boundary_values():
    """Test integer properties at their boundaries"""
    # Port numbers
    port = lightsail.Port()
    
    # Min port
    port.FromPort = 0
    assert port.FromPort == 0
    
    # Max port
    port.ToPort = 65535
    assert port.ToPort == 65535
    
    # Health check boundaries
    config = lightsail.HealthCheckConfig()
    
    config.HealthyThreshold = 2  # Min
    assert config.HealthyThreshold == 2
    
    config.UnhealthyThreshold = 10  # Max
    assert config.UnhealthyThreshold == 10
    
    config.TimeoutSeconds = 2  # Min
    assert config.TimeoutSeconds == 2
    
    config.TimeoutSeconds = 60  # Max
    assert config.TimeoutSeconds == 60

# Test property override
def test_property_override():
    """Properties should be overrideable"""
    disk = lightsail.Disk(
        title="TestDisk",
        DiskName="disk1",
        SizeInGb=16
    )
    
    # Override the size
    disk.SizeInGb = 32
    assert disk.SizeInGb == 32
    
    # Override again
    disk.SizeInGb = 64
    assert disk.SizeInGb == 64
    
    result = disk.to_dict()
    assert result["Properties"]["SizeInGb"] == 64

# Test nested property structures
def test_deeply_nested_properties():
    """Test deeply nested property structures"""
    # Create nested structure
    env_vars = []
    for i in range(10):
        env = lightsail.EnvironmentVariable()
        env.Variable = f"VAR_{i}"
        env.Value = f"value_{i}"
        env_vars.append(env)
    
    ports = []
    for i in range(5):
        port = lightsail.PortInfo()
        port.Port = str(8000 + i)
        port.Protocol = "tcp"
        ports.append(port)
    
    container = lightsail.ContainerProperty()
    container.ContainerName = "test"
    container.Image = "nginx"
    container.Environment = env_vars
    container.Ports = ports
    
    deployment = lightsail.ContainerServiceDeployment()
    deployment.Containers = [container]
    
    service = lightsail.Container(
        title="TestService",
        Power="nano",
        Scale=1,
        ServiceName="test",
        ContainerServiceDeployment=deployment
    )
    
    result = service.to_dict()
    containers = result["Properties"]["ContainerServiceDeployment"]["Containers"]
    assert len(containers) == 1
    assert len(containers[0]["Environment"]) == 10
    assert len(containers[0]["Ports"]) == 5

# Test title validation
def test_title_validation():
    """Resource titles should be alphanumeric only"""
    # Valid titles
    valid_titles = ["MyResource", "Resource123", "Test"]
    for title in valid_titles:
        instance = lightsail.Instance(
            title=title,
            BlueprintId="amazon_linux_2",
            BundleId="nano_2_0",
            InstanceName="test"
        )
        assert instance.title == title
    
    # Invalid titles should raise
    invalid_titles = ["My-Resource", "Resource_123", "Test!", "123 Test", ""]
    for title in invalid_titles:
        try:
            instance = lightsail.Instance(
                title=title,
                BlueprintId="amazon_linux_2",
                BundleId="nano_2_0",
                InstanceName="test"
            )
            assert False, f"Should have raised for title: {title}"
        except ValueError as e:
            assert "alphanumeric" in str(e).lower()

# Test template integration
def test_template_integration():
    """Resources should integrate with Template properly"""
    template = Template()
    
    # Add multiple resources
    instance = lightsail.Instance(
        title="MyInstance",
        template=template,
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName="test"
    )
    
    disk = lightsail.Disk(
        title="MyDisk",
        template=template,
        DiskName="disk1",
        SizeInGb=32
    )
    
    # Should be added to template
    json_output = template.to_json()
    parsed = json.loads(json_output)
    
    assert "MyInstance" in parsed["Resources"]
    assert "MyDisk" in parsed["Resources"]
    assert parsed["Resources"]["MyInstance"]["Type"] == "AWS::Lightsail::Instance"
    assert parsed["Resources"]["MyDisk"]["Type"] == "AWS::Lightsail::Disk"

# Test from_dict with invalid data
def test_from_dict_with_invalid_data():
    """from_dict should handle invalid data appropriately"""
    # Missing required properties
    try:
        alarm = lightsail.Alarm.from_dict("TestAlarm", {})
        alarm.to_dict()  # This should fail
        assert False, "Should have raised for missing required properties"
    except ValueError:
        pass
    
    # Invalid property names
    try:
        alarm = lightsail.Alarm.from_dict("TestAlarm", {
            "InvalidProperty": "value"
        })
        assert False, "Should have raised for invalid property"
    except AttributeError:
        pass

# Test boolean coercion edge case
def test_boolean_string_coercion():
    """Test boolean properties with string values '1' and '0'"""
    from troposphere.validators import boolean
    
    # These should work according to the validator
    assert boolean("1") is True  # This actually fails! "1" is not in the valid list
    assert boolean("0") is False  # This actually fails! "0" is not in the valid list

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])