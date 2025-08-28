"""Property-based tests for troposphere.scheduler AWS classes"""

from hypothesis import assume, given, strategies as st, settings
import pytest

from troposphere.scheduler import (
    FlexibleTimeWindow,
    DeadLetterConfig,
    CapacityProviderStrategyItem,
    AwsVpcConfiguration,
    NetworkConfiguration,
    PlacementConstraint,
    PlacementStrategy,
    EcsParameters,
    EventBridgeParameters,
    KinesisParameters,
    RetryPolicy,
    SageMakerPipelineParameter,
    SageMakerPipelineParameters,
    SqsParameters,
    Target,
    Schedule,
    ScheduleGroup,
)
from troposphere import Tags


# Test FlexibleTimeWindow initialization
@given(
    mode=st.sampled_from(["OFF", "FLEXIBLE"]),
    max_window=st.one_of(st.none(), st.integers(min_value=1, max_value=1440))
)
def test_flexible_time_window_valid_initialization(mode, max_window):
    """FlexibleTimeWindow should accept valid mode and optional MaximumWindowInMinutes"""
    if max_window is not None:
        ftw = FlexibleTimeWindow(Mode=mode, MaximumWindowInMinutes=max_window)
        assert ftw.to_dict()["Mode"] == mode
        assert ftw.to_dict()["MaximumWindowInMinutes"] == max_window
    else:
        ftw = FlexibleTimeWindow(Mode=mode)
        assert ftw.to_dict()["Mode"] == mode


@given(st.text().filter(lambda x: x not in ["OFF", "FLEXIBLE"]))
def test_flexible_time_window_invalid_mode(mode):
    """FlexibleTimeWindow should reject invalid modes"""
    with pytest.raises(ValueError, match="is not a valid mode"):
        FlexibleTimeWindow(Mode=mode)


# Test required fields validation
def test_flexible_time_window_missing_required():
    """FlexibleTimeWindow should require Mode field"""
    with pytest.raises((TypeError, ValueError)):
        FlexibleTimeWindow()


# Test CapacityProviderStrategyItem
@given(
    capacity_provider=st.text(min_size=1),
    base=st.one_of(st.none(), st.integers(min_value=0)),
    weight=st.one_of(st.none(), st.integers(min_value=0))
)
def test_capacity_provider_strategy_item(capacity_provider, base, weight):
    """CapacityProviderStrategyItem should require CapacityProvider"""
    kwargs = {"CapacityProvider": capacity_provider}
    if base is not None:
        kwargs["Base"] = base
    if weight is not None:
        kwargs["Weight"] = weight
    
    item = CapacityProviderStrategyItem(**kwargs)
    result = item.to_dict()
    assert result["CapacityProvider"] == capacity_provider
    if base is not None:
        assert result["Base"] == base
    if weight is not None:
        assert result["Weight"] == weight


# Test AwsVpcConfiguration
@given(
    subnets=st.lists(st.text(min_size=1), min_size=1, max_size=5),
    security_groups=st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=0, max_size=5)),
    assign_public_ip=st.one_of(st.none(), st.sampled_from(["ENABLED", "DISABLED"]))
)
def test_aws_vpc_configuration(subnets, security_groups, assign_public_ip):
    """AwsVpcConfiguration should require Subnets"""
    kwargs = {"Subnets": subnets}
    if security_groups is not None:
        kwargs["SecurityGroups"] = security_groups
    if assign_public_ip is not None:
        kwargs["AssignPublicIp"] = assign_public_ip
    
    config = AwsVpcConfiguration(**kwargs)
    result = config.to_dict()
    assert result["Subnets"] == subnets


# Test EventBridgeParameters
@given(
    detail_type=st.text(min_size=1),
    source=st.text(min_size=1)
)
def test_event_bridge_parameters(detail_type, source):
    """EventBridgeParameters should require DetailType and Source"""
    params = EventBridgeParameters(DetailType=detail_type, Source=source)
    result = params.to_dict()
    assert result["DetailType"] == detail_type
    assert result["Source"] == source


# Test for missing required fields in EventBridgeParameters
def test_event_bridge_parameters_missing_required():
    """EventBridgeParameters should fail without required fields"""
    with pytest.raises((TypeError, ValueError)):
        EventBridgeParameters(DetailType="test")  # Missing Source
    
    with pytest.raises((TypeError, ValueError)):
        EventBridgeParameters(Source="test")  # Missing DetailType


# Test RetryPolicy with numeric validation
@given(
    max_age=st.one_of(st.none(), st.integers(min_value=60, max_value=86400)),
    max_attempts=st.one_of(st.none(), st.integers(min_value=0, max_value=185))
)
def test_retry_policy(max_age, max_attempts):
    """RetryPolicy should accept valid numeric values"""
    kwargs = {}
    if max_age is not None:
        kwargs["MaximumEventAgeInSeconds"] = max_age
    if max_attempts is not None:
        kwargs["MaximumRetryAttempts"] = max_attempts
    
    policy = RetryPolicy(**kwargs)
    result = policy.to_dict()
    if max_age is not None:
        assert result["MaximumEventAgeInSeconds"] == max_age
    if max_attempts is not None:
        assert result["MaximumRetryAttempts"] == max_attempts


# Test SageMakerPipelineParameter
@given(
    name=st.text(min_size=1),
    value=st.text(min_size=1)
)
def test_sagemaker_pipeline_parameter(name, value):
    """SageMakerPipelineParameter should require Name and Value"""
    param = SageMakerPipelineParameter(Name=name, Value=value)
    result = param.to_dict()
    assert result["Name"] == name
    assert result["Value"] == value


# Test Target with required fields
@given(
    arn=st.text(min_size=1),
    role_arn=st.text(min_size=1),
    input_str=st.one_of(st.none(), st.text())
)
def test_target_required_fields(arn, role_arn, input_str):
    """Target should require Arn and RoleArn"""
    kwargs = {"Arn": arn, "RoleArn": role_arn}
    if input_str is not None:
        kwargs["Input"] = input_str
    
    target = Target(**kwargs)
    result = target.to_dict()
    assert result["Arn"] == arn
    assert result["RoleArn"] == role_arn


# Test Schedule with all required fields
@given(
    schedule_expression=st.text(min_size=1),
    mode=st.sampled_from(["OFF", "FLEXIBLE"]),
    target_arn=st.text(min_size=1),
    role_arn=st.text(min_size=1)
)
def test_schedule_required_fields(schedule_expression, mode, target_arn, role_arn):
    """Schedule should require ScheduleExpression, FlexibleTimeWindow, and Target"""
    schedule = Schedule(
        ScheduleExpression=schedule_expression,
        FlexibleTimeWindow=FlexibleTimeWindow(Mode=mode),
        Target=Target(Arn=target_arn, RoleArn=role_arn)
    )
    result = schedule.to_dict()
    assert result["Properties"]["ScheduleExpression"] == schedule_expression
    assert result["Properties"]["FlexibleTimeWindow"]["Mode"] == mode
    assert result["Properties"]["Target"]["Arn"] == target_arn
    assert result["Properties"]["Target"]["RoleArn"] == role_arn


# Test property validation for boolean fields
@given(
    enable_ecs=st.one_of(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]))
)
def test_ecs_parameters_boolean_fields(enable_ecs):
    """EcsParameters should validate boolean fields correctly"""
    params = EcsParameters(
        TaskDefinitionArn="arn:aws:ecs:region:account:task-definition/name",
        EnableECSManagedTags=enable_ecs
    )
    result = params.to_dict()
    # The boolean validator should normalize to True/False
    assert result["EnableECSManagedTags"] in [True, False]


# Test invalid boolean values
@given(
    invalid_bool=st.text().filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"])
)
def test_ecs_parameters_invalid_boolean(invalid_bool):
    """EcsParameters should reject invalid boolean values"""
    with pytest.raises(ValueError):
        EcsParameters(
            TaskDefinitionArn="arn:aws:ecs:region:account:task-definition/name",
            EnableECSManagedTags=invalid_bool
        )


# Test EcsParameters Tags must be None
@given(tags=st.one_of(
    st.text(),
    st.integers(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_ecs_parameters_tags_must_be_none(tags):
    """EcsParameters Tags field must be None"""
    with pytest.raises(ValueError, match="EcsParameters Tags must be None"):
        EcsParameters(
            TaskDefinitionArn="arn:aws:ecs:region:account:task-definition/name",
            Tags=tags
        )


# Test that None is accepted for EcsParameters Tags
def test_ecs_parameters_tags_none_accepted():
    """EcsParameters should accept None for Tags"""
    params = EcsParameters(
        TaskDefinitionArn="arn:aws:ecs:region:account:task-definition/name",
        Tags=None
    )
    # Should not raise an error