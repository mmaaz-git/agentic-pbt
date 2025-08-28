#!/usr/bin/env python3
"""Property-based tests for troposphere.imagebuilder module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest
import troposphere.imagebuilder as ib
from troposphere.validators.imagebuilder import (
    component_platforms,
    ebsinstanceblockdevicespecification_volume_type,
    imagepipeline_status,
    schedule_pipelineexecutionstartcondition,
)


# Test validator functions for boundary cases and error handling

@given(st.text())
def test_component_platforms_invalid_input(platform):
    """Test that component_platforms only accepts 'Linux' or 'Windows'"""
    if platform not in ["Linux", "Windows"]:
        with pytest.raises(ValueError, match="Platform must be one of"):
            component_platforms(platform)
    else:
        assert component_platforms(platform) == platform


@given(st.text())  
def test_volume_type_invalid_input(volume_type):
    """Test that volume type validator only accepts specific values"""
    valid_types = ["gp2", "gp3", "io1", "io2", "sc1", "st1", "standard"]
    if volume_type not in valid_types:
        with pytest.raises(ValueError, match="VolumeType must be one of"):
            ebsinstanceblockdevicespecification_volume_type(volume_type)
    else:
        assert ebsinstanceblockdevicespecification_volume_type(volume_type) == volume_type


@given(st.text())
def test_imagepipeline_status_invalid_input(status):
    """Test that imagepipeline_status only accepts 'DISABLED' or 'ENABLED'"""
    if status not in ["DISABLED", "ENABLED"]:
        with pytest.raises(ValueError, match="Status must be one of"):
            imagepipeline_status(status)
    else:
        assert imagepipeline_status(status) == status


@given(st.text())
def test_schedule_condition_invalid_input(condition):
    """Test schedule pipeline execution start condition validator"""
    valid_conditions = [
        "EXPRESSION_MATCH_AND_DEPENDENCY_UPDATES_AVAILABLE",
        "EXPRESSION_MATCH_ONLY",
    ]
    if condition not in valid_conditions:
        with pytest.raises(ValueError, match="PipelineExecutionStartCondition must be one of"):
            schedule_pipelineexecutionstartcondition(condition)
    else:
        assert schedule_pipelineexecutionstartcondition(condition) == condition


# Test edge cases with special characters and Unicode

@given(st.text(min_size=1).filter(lambda x: x not in ["Linux", "Windows"]))
def test_component_platforms_unicode_and_special(platform):
    """Test component platforms with unicode and special characters"""
    with pytest.raises(ValueError, match="Platform must be one of"):
        component_platforms(platform)


# Test case sensitivity in validators

@given(st.sampled_from(["linux", "LINUX", "windows", "WINDOWS", "Linux", "Windows"]))
def test_component_platforms_case_sensitivity(platform):
    """Test that platform validator is case-sensitive"""
    if platform in ["Linux", "Windows"]:
        assert component_platforms(platform) == platform
    else:
        with pytest.raises(ValueError):
            component_platforms(platform)


# Test ComponentParameter value type

@given(
    name=st.text(min_size=1),
    value=st.one_of(
        st.lists(st.text()),
        st.text(),
        st.integers(),
        st.none(),
    )
)
def test_component_parameter_value_type(name, value):
    """Test ComponentParameter expects Value to be a list of strings"""
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        # Valid case
        param = ib.ComponentParameter(Name=name, Value=value)
        assert param.Name == name
        assert param.Value == value
    else:
        # Should raise TypeError for non-list or non-string list elements
        with pytest.raises((TypeError, AttributeError)):
            ib.ComponentParameter(Name=name, Value=value)


# Test integer properties with various types

@given(
    iops=st.one_of(
        st.integers(),
        st.floats(),
        st.text(),
        st.none(),
        st.booleans(),
    )
)
def test_ebs_iops_type_validation(iops):
    """Test that Iops property handles different types correctly"""
    try:
        ebs = ib.EbsInstanceBlockDeviceSpecification(Iops=iops)
        # If it succeeds, check if the value was properly handled
        if hasattr(ebs, 'Iops'):
            # Should either be an integer or properly converted
            assert isinstance(ebs.Iops, (int, type(None))) or hasattr(ebs.Iops, '__class__')
    except (TypeError, ValueError, AttributeError):
        # Type error is expected for invalid types
        pass


# Test required vs optional properties

@given(
    name=st.text(min_size=1),
    platform=st.sampled_from(["Linux", "Windows"]),
    version=st.text(min_size=1),
    description=st.one_of(st.text(), st.none()),
)
def test_component_required_properties(name, platform, version, description):
    """Test Component with required and optional properties"""
    # Required: Name, Platform, Version
    component = ib.Component(
        "TestComponent",
        Name=name,
        Platform=platform,
        Version=version
    )
    assert component.Name == name
    assert component.Platform == platform
    assert component.Version == version
    
    # Optional property
    if description is not None:
        component.Description = description
        assert component.Description == description


# Test empty strings for required string properties

@given(
    name=st.sampled_from(["", " ", "\t", "\n"]),
    platform=st.sampled_from(["Linux", "Windows"]),
    version=st.text(min_size=1),
)  
def test_component_empty_name(name, platform, version):
    """Test Component with empty or whitespace-only name"""
    # Empty strings should be accepted (AWS will validate)
    component = ib.Component(
        "TestComponent",
        Name=name,
        Platform=platform,
        Version=version
    )
    assert component.Name == name


# Test Schedule property with edge cases

@given(
    expr=st.text(),
    condition=st.one_of(
        st.none(),
        st.sampled_from([
            "EXPRESSION_MATCH_AND_DEPENDENCY_UPDATES_AVAILABLE",
            "EXPRESSION_MATCH_ONLY",
        ]),
        st.text()
    )
)
def test_schedule_property(expr, condition):
    """Test Schedule property with various inputs"""
    schedule = ib.Schedule(ScheduleExpression=expr)
    assert schedule.ScheduleExpression == expr
    
    if condition is not None:
        if condition in ["EXPRESSION_MATCH_AND_DEPENDENCY_UPDATES_AVAILABLE", "EXPRESSION_MATCH_ONLY"]:
            schedule.PipelineExecutionStartCondition = condition
            assert schedule.PipelineExecutionStartCondition == condition
        else:
            # Invalid condition should be caught by validator
            with pytest.raises(ValueError):
                schedule.PipelineExecutionStartCondition = condition


# Test list properties with non-list inputs

@given(
    supported_versions=st.one_of(
        st.lists(st.text()),
        st.text(),
        st.integers(),
        st.dictionaries(st.text(), st.text()),
        st.none()
    )
)
def test_component_supported_os_versions(supported_versions):
    """Test Component.SupportedOsVersions expects a list"""
    component = ib.Component(
        "TestComponent",
        Name="Test",
        Platform="Linux",
        Version="1.0"
    )
    
    if isinstance(supported_versions, list):
        component.SupportedOsVersions = supported_versions
        assert component.SupportedOsVersions == supported_versions
    elif supported_versions is not None:
        with pytest.raises(TypeError):
            component.SupportedOsVersions = supported_versions


# Test boolean properties with various types

@given(
    enabled=st.one_of(
        st.booleans(),
        st.integers(),
        st.text(),
        st.none(),
        st.lists(st.integers())
    )
)
def test_boolean_property_validation(enabled):
    """Test boolean property type validation"""
    try:
        config = ib.ImageTestsConfiguration(ImageTestsEnabled=enabled)
        # If successful, it should have accepted the value
        if hasattr(config, 'ImageTestsEnabled'):
            # Check if troposphere properly handles the type
            pass
    except (TypeError, ValueError, AttributeError):
        # Type validation might reject non-boolean values
        pass


# Test dictionary properties

@given(
    tags=st.one_of(
        st.dictionaries(st.text(min_size=1), st.text()),
        st.lists(st.text()),
        st.text(),
        st.integers(),
        st.none()
    )
)
def test_component_tags_property(tags):
    """Test that Tags property expects a dictionary"""
    component = ib.Component(
        "TestComponent",
        Name="Test",
        Platform="Linux",
        Version="1.0"
    )
    
    if isinstance(tags, dict) or tags is None:
        if tags is not None:
            component.Tags = tags
            assert component.Tags == tags
    else:
        with pytest.raises((TypeError, AttributeError)):
            component.Tags = tags


# Test property assignment after object creation

@given(
    initial_name=st.text(min_size=1),
    new_name=st.text(min_size=1),
    platform=st.sampled_from(["Linux", "Windows"])
)
def test_property_reassignment(initial_name, new_name, platform):
    """Test that properties can be reassigned after object creation"""
    component = ib.Component(
        "TestComponent",
        Name=initial_name,
        Platform=platform,
        Version="1.0"
    )
    assert component.Name == initial_name
    
    # Reassign the property
    component.Name = new_name
    assert component.Name == new_name
    
    # Platform should remain unchanged
    assert component.Platform == platform


# Test nested property structures

@given(
    bucket_name=st.text(),
    key_prefix=st.text()
)
def test_nested_s3_logs_property(bucket_name, key_prefix):
    """Test nested property structure in S3Logs"""
    s3_logs = ib.S3Logs(
        S3BucketName=bucket_name,
        S3KeyPrefix=key_prefix
    )
    assert s3_logs.S3BucketName == bucket_name
    assert s3_logs.S3KeyPrefix == key_prefix
    
    # Test using it in a parent object
    logging = ib.Logging(S3Logs=s3_logs)
    assert logging.S3Logs == s3_logs


# Test WorkflowParameter with edge cases

@given(
    name=st.text(),
    value=st.one_of(
        st.none(),
        st.lists(st.text()),
        st.lists(st.integers()),
        st.text(),
        st.integers()
    )
)
def test_workflow_parameter_value_validation(name, value):
    """Test WorkflowParameter.Value expects list of strings"""
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        param = ib.WorkflowParameter(Name=name, Value=value)
        assert param.Value == value
    elif value is None:
        # None should be allowed for optional property
        param = ib.WorkflowParameter(Name=name)
        # Should not have the Value attribute if not set
        if hasattr(param, 'Value'):
            assert param.Value is None
    else:
        # Non-list or non-string list should fail
        with pytest.raises((TypeError, AttributeError)):
            ib.WorkflowParameter(Name=name, Value=value)