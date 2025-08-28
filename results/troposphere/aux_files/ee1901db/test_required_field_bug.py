"""Test to confirm required field validation bug in troposphere.scheduler"""

from hypothesis import given, strategies as st
import pytest

from troposphere.scheduler import (
    FlexibleTimeWindow,
    EventBridgeParameters,
    KinesisParameters,
    SageMakerPipelineParameter,
    CapacityProviderStrategyItem,
    AwsVpcConfiguration,
    Target,
    EcsParameters,
)


# Test that required fields are NOT validated at initialization
def test_flexible_time_window_deferred_validation():
    """BUG: FlexibleTimeWindow allows creation without required Mode field"""
    # This should fail but doesn't
    ftw = FlexibleTimeWindow()
    
    # The validation only happens when calling to_dict()
    with pytest.raises(ValueError, match="Resource Mode required"):
        ftw.to_dict()


def test_event_bridge_parameters_deferred_validation():
    """BUG: EventBridgeParameters allows partial initialization"""
    # Missing Source - should fail but doesn't
    ebp1 = EventBridgeParameters(DetailType="test")
    with pytest.raises(ValueError, match="Resource Source required"):
        ebp1.to_dict()
    
    # Missing DetailType - should fail but doesn't
    ebp2 = EventBridgeParameters(Source="test")
    with pytest.raises(ValueError, match="Resource DetailType required"):
        ebp2.to_dict()


def test_kinesis_parameters_deferred_validation():
    """BUG: KinesisParameters allows creation without required PartitionKey"""
    kp = KinesisParameters()
    with pytest.raises(ValueError, match="Resource PartitionKey required"):
        kp.to_dict()


def test_sagemaker_pipeline_parameter_deferred_validation():
    """BUG: SageMakerPipelineParameter allows partial initialization"""
    # Missing Value
    sp1 = SageMakerPipelineParameter(Name="test")
    with pytest.raises(ValueError, match="Resource Value required"):
        sp1.to_dict()
    
    # Missing Name
    sp2 = SageMakerPipelineParameter(Value="test")
    with pytest.raises(ValueError, match="Resource Name required"):
        sp2.to_dict()


def test_capacity_provider_strategy_item_deferred_validation():
    """BUG: CapacityProviderStrategyItem allows creation without required CapacityProvider"""
    item = CapacityProviderStrategyItem()
    with pytest.raises(ValueError, match="Resource CapacityProvider required"):
        item.to_dict()


def test_aws_vpc_configuration_deferred_validation():
    """BUG: AwsVpcConfiguration allows creation without required Subnets"""
    config = AwsVpcConfiguration()
    with pytest.raises(ValueError, match="Resource Subnets required"):
        config.to_dict()


def test_target_deferred_validation():
    """BUG: Target allows partial initialization"""
    # Missing RoleArn
    t1 = Target(Arn="arn:aws:lambda:us-east-1:123456789012:function:MyFunction")
    with pytest.raises(ValueError, match="Resource RoleArn required"):
        t1.to_dict()
    
    # Missing Arn
    t2 = Target(RoleArn="arn:aws:iam::123456789012:role/MyRole")
    with pytest.raises(ValueError, match="Resource Arn required"):
        t2.to_dict()


def test_ecs_parameters_deferred_validation():
    """BUG: EcsParameters allows creation without required TaskDefinitionArn"""
    params = EcsParameters()
    with pytest.raises(ValueError, match="Resource TaskDefinitionArn required"):
        params.to_dict()


# Property test: All classes with required fields show deferred validation
@given(st.sampled_from([
    FlexibleTimeWindow,
    EventBridgeParameters,
    KinesisParameters,
    SageMakerPipelineParameter,
    CapacityProviderStrategyItem,
    AwsVpcConfiguration,
    Target,
    EcsParameters
]))
def test_all_classes_have_deferred_validation(cls):
    """All classes allow instantiation without required fields"""
    # This should ideally fail during __init__ but doesn't
    instance = cls()
    
    # The error only happens when calling to_dict()
    with pytest.raises(ValueError, match="Resource .* required"):
        instance.to_dict()


# Demonstrate the confusion this can cause
def test_confusing_error_location():
    """BUG: Errors appear far from where the mistake was made"""
    # Developer creates an object without required fields
    ftw = FlexibleTimeWindow()  # No error here - seems fine!
    
    # ... many lines of code later ...
    # ... possibly in a different function ...
    # ... possibly in a different file ...
    
    # Only NOW does the error appear
    with pytest.raises(ValueError):
        ftw.to_dict()  # Error appears here, far from the source