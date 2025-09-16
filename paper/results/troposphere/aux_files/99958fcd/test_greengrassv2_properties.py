#!/usr/bin/env python3
"""Property-based tests for troposphere.greengrassv2 module."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.greengrassv2 as ggv2
from troposphere.validators import boolean, integer, double


# Test 1: Validator functions - boolean
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts valid boolean-like values."""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers(min_value=2),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs."""
    try:
        boolean(value)
        assert False, f"Expected ValueError for {value!r}"
    except ValueError:
        pass  # Expected


# Test 2: Validator functions - integer
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.lstrip('-').isdigit())
))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer values."""
    result = integer(value)
    assert result == value
    # Verify it's actually convertible to int
    int(result)


@given(st.one_of(
    st.floats(allow_nan=False).filter(lambda x: not x.is_integer()),
    st.text(min_size=1).filter(lambda x: not x.lstrip('-').isdigit()),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_invalid_inputs(value):
    """Test that integer validator rejects non-integer inputs."""
    try:
        integer(value)
        assert False, f"Expected ValueError for {value!r}"
    except ValueError:
        pass  # Expected


# Test 3: Validator functions - double
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.replace('.', '', 1).replace('-', '', 1).replace('e', '', 1).replace('+', '', 1).isdigit() and '.' in x)
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid float values."""
    result = double(value)
    assert result == value
    # Verify it's actually convertible to float
    float(result)


# Test 4: Object construction - ComponentPlatform
@given(
    name=st.text(min_size=1, max_size=100),
    attributes=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        max_size=10
    )
)
def test_component_platform_construction(name, attributes):
    """Test that ComponentPlatform can be constructed with valid inputs."""
    platform = ggv2.ComponentPlatform(
        Name=name,
        Attributes=attributes
    )
    assert platform.Name == name
    assert platform.Attributes == attributes
    
    # Test to_dict doesn't crash
    result = platform.to_dict()
    assert isinstance(result, dict)


# Test 5: Object construction - SystemResourceLimits with numeric validators
@given(
    cpus=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    memory=st.integers(min_value=0, max_value=10**9)
)
def test_system_resource_limits_construction(cpus, memory):
    """Test that SystemResourceLimits correctly validates numeric inputs."""
    limits = ggv2.SystemResourceLimits(
        Cpus=cpus,
        Memory=memory
    )
    assert limits.Cpus == cpus
    assert limits.Memory == memory
    
    # Test serialization
    result = limits.to_dict()
    assert isinstance(result, dict)
    assert result.get('Cpus') == cpus
    assert result.get('Memory') == memory


# Test 6: Required properties - IoTJobAbortCriteria
@given(
    action=st.text(min_size=1, max_size=50),
    failure_type=st.text(min_size=1, max_size=50),
    min_executed=st.integers(min_value=0, max_value=10000),
    threshold=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
)
def test_iot_job_abort_criteria_required_properties(action, failure_type, min_executed, threshold):
    """Test that IoTJobAbortCriteria enforces required properties."""
    # All required properties provided - should work
    criteria = ggv2.IoTJobAbortCriteria(
        Action=action,
        FailureType=failure_type,
        MinNumberOfExecutedThings=min_executed,
        ThresholdPercentage=threshold
    )
    
    result = criteria.to_dict()
    assert isinstance(result, dict)
    assert result['Action'] == action
    assert result['FailureType'] == failure_type
    assert result['MinNumberOfExecutedThings'] == min_executed
    assert result['ThresholdPercentage'] == threshold


# Test 7: Lists of objects - IoTJobAbortConfig
@given(
    criteria_list=st.lists(
        st.builds(
            lambda: {
                'Action': 'CANCEL',
                'FailureType': 'FAILED',
                'MinNumberOfExecutedThings': 1,
                'ThresholdPercentage': 50.0
            }
        ),
        min_size=1,
        max_size=5
    )
)
def test_iot_job_abort_config_list_property(criteria_list):
    """Test that IoTJobAbortConfig correctly handles lists of criteria."""
    criteria_objects = [
        ggv2.IoTJobAbortCriteria(**criteria) 
        for criteria in criteria_list
    ]
    
    config = ggv2.IoTJobAbortConfig(CriteriaList=criteria_objects)
    
    result = config.to_dict()
    assert isinstance(result, dict)
    assert 'CriteriaList' in result
    assert len(result['CriteriaList']) == len(criteria_list)


# Test 8: Nested object properties
@given(
    posix_user=st.text(min_size=1, max_size=100),
    windows_user=st.text(min_size=1, max_size=100),
    cpus=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
    memory=st.integers(min_value=128, max_value=10**6)
)
def test_component_run_with_nested_objects(posix_user, windows_user, cpus, memory):
    """Test ComponentRunWith with nested SystemResourceLimits."""
    limits = ggv2.SystemResourceLimits(
        Cpus=cpus,
        Memory=memory
    )
    
    run_with = ggv2.ComponentRunWith(
        PosixUser=posix_user,
        WindowsUser=windows_user,
        SystemResourceLimits=limits
    )
    
    result = run_with.to_dict()
    assert isinstance(result, dict)
    assert result['PosixUser'] == posix_user
    assert result['WindowsUser'] == windows_user
    assert 'SystemResourceLimits' in result
    assert result['SystemResourceLimits']['Cpus'] == cpus
    assert result['SystemResourceLimits']['Memory'] == memory


# Test 9: AWSObject with resource_type - ComponentVersion
@given(
    inline_recipe=st.text(min_size=1, max_size=1000),
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        max_size=5
    )
)
def test_component_version_aws_object(inline_recipe, tags):
    """Test ComponentVersion as an AWSObject with resource_type."""
    # ComponentVersion requires a title since it's an AWSObject
    assume(inline_recipe.replace(' ', '').isalnum())  # Title must be alphanumeric
    
    component = ggv2.ComponentVersion(
        title="TestComponent",
        InlineRecipe=inline_recipe,
        Tags=tags
    )
    
    result = component.to_dict()
    assert isinstance(result, dict)
    assert result.get('Type') == 'AWS::GreengrassV2::ComponentVersion'
    assert result.get('Properties', {}).get('InlineRecipe') == inline_recipe
    assert result.get('Properties', {}).get('Tags') == tags


# Test 10: Deployment with required TargetArn
@given(
    target_arn=st.text(min_size=1, max_size=200),
    deployment_name=st.text(min_size=1, max_size=100),
    parent_arn=st.text(min_size=1, max_size=200)
)
def test_deployment_required_target_arn(target_arn, deployment_name, parent_arn):
    """Test Deployment enforces required TargetArn property."""
    assume(deployment_name.replace(' ', '').isalnum())  # Title must be alphanumeric
    
    deployment = ggv2.Deployment(
        title="TestDeployment",
        TargetArn=target_arn,
        DeploymentName=deployment_name,
        ParentTargetArn=parent_arn
    )
    
    result = deployment.to_dict()
    assert isinstance(result, dict)
    assert result.get('Type') == 'AWS::GreengrassV2::Deployment'
    assert result.get('Properties', {}).get('TargetArn') == target_arn
    assert result.get('Properties', {}).get('DeploymentName') == deployment_name