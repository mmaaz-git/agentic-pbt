#!/usr/bin/env python3
"""Property-based tests for troposphere.iotcoredeviceadvisor module"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import string

# Add the environment path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.iotcoredeviceadvisor as iotcore
from troposphere import Template, Tags
from troposphere.validators import boolean


# Strategies for generating valid AWS ARNs
arn_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + ":/-_",
    min_size=20,
    max_size=200
).filter(lambda x: x.startswith("arn:"))


# Strategies for valid CloudFormation resource names (alphanumeric only)
valid_title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=50
)


# Invalid title strategy - includes non-alphanumeric characters
invalid_title_strategy = st.one_of(
    st.text(min_size=1, max_size=50).filter(lambda x: not x.isalnum()),
    st.just(""),
    st.just("test-name"),
    st.just("test_name"),
    st.just("test.name"),
    st.just("123!@#"),
)


# Test 1: Round-trip serialization property for DeviceUnderTest
@given(
    cert_arn=st.one_of(st.none(), arn_strategy),
    thing_arn=st.one_of(st.none(), arn_strategy)
)
def test_device_under_test_roundtrip(cert_arn, thing_arn):
    """Test that DeviceUnderTest objects serialize to dict and back correctly"""
    # Create object with optional parameters
    kwargs = {}
    if cert_arn is not None:
        kwargs['CertificateArn'] = cert_arn
    if thing_arn is not None:
        kwargs['ThingArn'] = thing_arn
    
    device = iotcore.DeviceUnderTest(**kwargs)
    
    # Serialize to dict
    device_dict = device.to_dict()
    
    # Verify the dict contains the expected values
    if cert_arn is not None:
        assert device_dict.get('CertificateArn') == cert_arn
    if thing_arn is not None:
        assert device_dict.get('ThingArn') == thing_arn
    
    # Create a new object from the dict
    device2 = iotcore.DeviceUnderTest(**device_dict)
    
    # Verify they serialize to the same dict
    assert device.to_dict() == device2.to_dict()


# Test 2: Required field validation for SuiteDefinitionConfiguration
@given(
    device_role=st.one_of(st.none(), arn_strategy),
    root_group=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    suite_name=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
)
def test_suite_definition_config_required_fields(device_role, root_group, suite_name):
    """Test that required fields are validated in SuiteDefinitionConfiguration"""
    kwargs = {}
    
    # Add optional field
    if suite_name is not None:
        kwargs['SuiteDefinitionName'] = suite_name
    
    # DevicePermissionRoleArn and RootGroup are required
    if device_role is not None:
        kwargs['DevicePermissionRoleArn'] = device_role
    if root_group is not None:
        kwargs['RootGroup'] = root_group
    
    # Should only succeed if both required fields are present
    should_succeed = (device_role is not None and root_group is not None)
    
    if should_succeed:
        config = iotcore.SuiteDefinitionConfiguration(**kwargs)
        # Should be able to serialize without error
        config_dict = config.to_dict()
        assert 'DevicePermissionRoleArn' in config_dict
        assert 'RootGroup' in config_dict
    else:
        # Should raise ValueError for missing required field
        try:
            config = iotcore.SuiteDefinitionConfiguration(**kwargs)
            config.to_dict()  # Validation happens on to_dict()
            # If we get here, validation didn't work as expected
            assert False, f"Expected validation error but succeeded with kwargs: {kwargs}"
        except ValueError as e:
            # Expected behavior - required field missing
            assert "required" in str(e).lower()


# Test 3: Boolean validator property
@given(
    bool_input=st.one_of(
        st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"]),
        st.text(min_size=1, max_size=20),  # Random text to test invalid inputs
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.none(),
    )
)
def test_boolean_validator(bool_input):
    """Test that the boolean validator handles various inputs correctly"""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if bool_input in valid_true:
        assert boolean(bool_input) is True
    elif bool_input in valid_false:
        assert boolean(bool_input) is False
    else:
        # Should raise ValueError for invalid inputs
        try:
            result = boolean(bool_input)
            # If we get here, the validator accepted an invalid input
            assert False, f"Boolean validator accepted invalid input: {bool_input} -> {result}"
        except (ValueError, TypeError):
            # Expected behavior for invalid input
            pass


# Test 4: Title validation for AWS resources
@given(title=st.one_of(valid_title_strategy, invalid_title_strategy))
def test_suite_definition_title_validation(title):
    """Test that resource titles must be alphanumeric"""
    # SuiteDefinition requires a SuiteDefinitionConfiguration
    config = iotcore.SuiteDefinitionConfiguration(
        DevicePermissionRoleArn="arn:aws:iam::123456789012:role/TestRole",
        RootGroup="TestGroup"
    )
    
    is_valid_title = title and title.isalnum()
    
    if is_valid_title:
        # Should succeed with valid title
        suite = iotcore.SuiteDefinition(
            title=title,
            SuiteDefinitionConfiguration=config
        )
        # Title should be set correctly
        assert suite.title == title
    else:
        # Should raise ValueError for invalid title
        try:
            suite = iotcore.SuiteDefinition(
                title=title,
                SuiteDefinitionConfiguration=config
            )
            assert False, f"Expected validation error for invalid title: {repr(title)}"
        except ValueError as e:
            assert "alphanumeric" in str(e).lower()


# Test 5: Complex object nesting and serialization
@given(
    cert_arns=st.lists(arn_strategy, min_size=0, max_size=5),
    thing_arns=st.lists(arn_strategy, min_size=0, max_size=5),
    intended_for_qual=st.one_of(st.none(), st.booleans(), st.sampled_from([1, 0, "true", "false"])),
    suite_name=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_suite_definition_complex_serialization(cert_arns, thing_arns, intended_for_qual, suite_name):
    """Test complex nested object serialization with SuiteDefinition"""
    # Create devices
    devices = []
    for i in range(min(len(cert_arns), len(thing_arns))):
        device = iotcore.DeviceUnderTest(
            CertificateArn=cert_arns[i],
            ThingArn=thing_arns[i]
        )
        devices.append(device)
    
    # Build configuration kwargs
    config_kwargs = {
        'DevicePermissionRoleArn': 'arn:aws:iam::123456789012:role/TestRole',
        'RootGroup': 'TestRootGroup'
    }
    
    if devices:
        config_kwargs['Devices'] = devices
    
    if intended_for_qual is not None:
        # Test the boolean validator within the context
        try:
            config_kwargs['IntendedForQualification'] = boolean(intended_for_qual)
        except (ValueError, TypeError):
            # Skip invalid boolean values
            return
    
    if suite_name is not None:
        config_kwargs['SuiteDefinitionName'] = suite_name
    
    # Create the configuration
    config = iotcore.SuiteDefinitionConfiguration(**config_kwargs)
    
    # Create the suite definition
    suite = iotcore.SuiteDefinition(
        title="TestSuite",
        SuiteDefinitionConfiguration=config
    )
    
    # Serialize to dict
    suite_dict = suite.to_dict()
    
    # Verify structure
    assert 'Type' in suite_dict
    assert suite_dict['Type'] == 'AWS::IoTCoreDeviceAdvisor::SuiteDefinition'
    assert 'Properties' in suite_dict
    props = suite_dict['Properties']
    assert 'SuiteDefinitionConfiguration' in props
    
    config_dict = props['SuiteDefinitionConfiguration']
    assert config_dict['DevicePermissionRoleArn'] == 'arn:aws:iam::123456789012:role/TestRole'
    assert config_dict['RootGroup'] == 'TestRootGroup'
    
    if devices:
        assert 'Devices' in config_dict
        assert len(config_dict['Devices']) == len(devices)
    
    # Verify JSON serialization works
    json_str = json.dumps(suite_dict)
    parsed = json.loads(json_str)
    assert parsed == suite_dict


# Test 6: Type validation for fields
@given(
    invalid_devices=st.one_of(
        st.text(),  # String instead of list
        st.integers(),  # Integer instead of list
        st.dictionaries(st.text(), st.text()),  # Dict instead of list
        st.lists(st.text()),  # List of strings instead of DeviceUnderTest objects
    )
)
def test_suite_config_devices_type_validation(invalid_devices):
    """Test that Devices field validates type correctly"""
    try:
        config = iotcore.SuiteDefinitionConfiguration(
            DevicePermissionRoleArn='arn:aws:iam::123456789012:role/TestRole',
            RootGroup='TestGroup',
            Devices=invalid_devices
        )
        # If it doesn't fail immediately, it might fail on to_dict()
        config.to_dict()
        
        # Check if the invalid value was silently accepted
        if not isinstance(invalid_devices, list):
            assert False, f"Expected type error for non-list Devices: {type(invalid_devices)}"
    except (TypeError, AttributeError) as e:
        # Expected behavior - type validation failed
        pass


if __name__ == "__main__":
    print("Running property-based tests for troposphere.iotcoredeviceadvisor...")
    import pytest
    pytest.main([__file__, "-v"])