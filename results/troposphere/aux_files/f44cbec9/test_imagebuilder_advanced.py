#!/usr/bin/env python3
"""Advanced property-based tests for troposphere.imagebuilder module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings, example
import pytest
import json
import troposphere.imagebuilder as ib
from troposphere import AWSHelperFn, Base64, Ref, Sub, GetAtt


# Test serialization/deserialization round-trip

@given(
    name=st.text(min_size=1, max_size=100),
    platform=st.sampled_from(["Linux", "Windows"]),
    version=st.text(min_size=1, max_size=20),
    description=st.one_of(st.none(), st.text(max_size=500)),
    change_desc=st.one_of(st.none(), st.text(max_size=500)),
)
def test_component_to_dict_roundtrip(name, platform, version, description, change_desc):
    """Test Component serialization to dict"""
    component = ib.Component(
        "TestComponent",
        Name=name,
        Platform=platform,
        Version=version
    )
    
    if description is not None:
        component.Description = description
    if change_desc is not None:
        component.ChangeDescription = change_desc
    
    # Serialize to dict
    comp_dict = component.to_dict()
    
    # Should have required fields
    assert "Type" in comp_dict
    assert comp_dict["Type"] == "AWS::ImageBuilder::Component"
    assert "Properties" in comp_dict
    assert comp_dict["Properties"]["Name"] == name
    assert comp_dict["Properties"]["Platform"] == platform
    assert comp_dict["Properties"]["Version"] == version
    
    # Optional fields
    if description is not None:
        assert comp_dict["Properties"]["Description"] == description
    if change_desc is not None:
        assert comp_dict["Properties"]["ChangeDescription"] == change_desc


# Test JSON serialization with special characters

@given(
    name=st.text(min_size=1).filter(lambda x: any(c in x for c in ['"', '\\', '\n', '\r', '\t'])),
    platform=st.sampled_from(["Linux", "Windows"]),
    version=st.text(min_size=1)
)
def test_component_json_special_chars(name, platform, version):
    """Test JSON serialization with special characters"""
    component = ib.Component(
        "TestComponent",
        Name=name,
        Platform=platform,
        Version=version
    )
    
    # Should serialize to valid JSON
    json_str = component.to_json()
    parsed = json.loads(json_str)
    
    # Should preserve the special characters
    assert parsed["Properties"]["Name"] == name


# Test complex nested structures

@given(
    repo_name=st.text(min_size=1),
    service=st.text(min_size=1),
    container_tags=st.lists(st.text(min_size=1), max_size=10),
    description=st.one_of(st.none(), st.text())
)
def test_container_distribution_nested(repo_name, service, container_tags, description):
    """Test nested ContainerDistributionConfiguration"""
    target_repo = ib.TargetContainerRepository(
        RepositoryName=repo_name,
        Service=service
    )
    
    config = ib.ContainerDistributionConfiguration(
        TargetRepository=target_repo,
        ContainerTags=container_tags
    )
    
    if description is not None:
        config.Description = description
    
    # Verify nested structure
    assert config.TargetRepository == target_repo
    assert config.ContainerTags == container_tags
    
    # Test in parent Distribution object
    distribution = ib.Distribution(
        Region="us-west-2",
        ContainerDistributionConfiguration=config
    )
    
    # Serialize and check structure
    dist_dict = distribution.to_dict()
    assert "Region" in dist_dict
    assert "ContainerDistributionConfiguration" in dist_dict


# Test with AWS helper functions

@given(
    name=st.text(min_size=1),
    platform=st.sampled_from(["Linux", "Windows"]),
    version=st.text(min_size=1)
)
def test_component_with_aws_helpers(name, platform, version):
    """Test Component with AWS helper functions like Ref"""
    component = ib.Component(
        "TestComponent",
        Name=Ref("ComponentName"),  # Use CloudFormation reference
        Platform=platform,
        Version=version,
        KmsKeyId=Ref("KmsKey")
    )
    
    # AWS helper functions should be preserved
    assert isinstance(component.Name, Ref)
    assert isinstance(component.KmsKeyId, Ref)
    
    # Should serialize correctly
    comp_dict = component.to_dict()
    assert "Ref" in comp_dict["Properties"]["Name"]
    assert comp_dict["Properties"]["Name"]["Ref"] == "ComponentName"


# Test validation of integer properties with extreme values

@given(
    iops=st.one_of(
        st.integers(min_value=-2**63, max_value=2**63),
        st.floats(allow_nan=True, allow_infinity=True)
    ),
    throughput=st.one_of(
        st.integers(min_value=-2**63, max_value=2**63),
        st.floats(allow_nan=True, allow_infinity=True)
    ),
    volume_size=st.one_of(
        st.integers(min_value=-2**63, max_value=2**63),
        st.floats(allow_nan=True, allow_infinity=True)
    )
)
def test_ebs_extreme_numeric_values(iops, throughput, volume_size):
    """Test EBS configuration with extreme numeric values"""
    ebs = ib.EbsInstanceBlockDeviceSpecification()
    
    # Test setting extreme values
    for value, prop_name in [(iops, 'Iops'), (throughput, 'Throughput'), (volume_size, 'VolumeSize')]:
        if isinstance(value, int):
            setattr(ebs, prop_name, value)
            assert getattr(ebs, prop_name) == value
        elif isinstance(value, float):
            # Float values for integer properties might raise TypeError
            try:
                setattr(ebs, prop_name, value)
                # If accepted, check the value
                stored_value = getattr(ebs, prop_name)
                # Might be converted to int or kept as float
            except (TypeError, ValueError):
                pass  # Expected for non-integer values


# Test LastLaunched with boundary values

@given(
    unit=st.text(),
    value=st.one_of(
        st.integers(),
        st.floats(),
        st.text(),
        st.none()
    )
)
def test_last_launched_validation(unit, value):
    """Test LastLaunched property validation"""
    if isinstance(value, int):
        last_launched = ib.LastLaunched(Unit=unit, Value=value)
        assert last_launched.Unit == unit
        assert last_launched.Value == value
    else:
        # Non-integer values should fail
        with pytest.raises((TypeError, ValueError, AttributeError)):
            ib.LastLaunched(Unit=unit, Value=value)


# Test PolicyDetail with all combinations

@given(
    action_type=st.text(min_size=1),
    include_amis=st.booleans(),
    include_containers=st.booleans(),
    include_snapshots=st.booleans(),
    filter_type=st.text(min_size=1),
    filter_value=st.integers(),
    filter_unit=st.one_of(st.none(), st.text()),
    retain_at_least=st.one_of(st.none(), st.integers())
)
def test_policy_detail_complex(action_type, include_amis, include_containers, 
                               include_snapshots, filter_type, filter_value,
                               filter_unit, retain_at_least):
    """Test PolicyDetail with complex nested structures"""
    # Create IncludeResources
    include = ib.IncludeResources(
        Amis=include_amis,
        Containers=include_containers,
        Snapshots=include_snapshots
    )
    
    # Create Action
    action = ib.Action(
        Type=action_type,
        IncludeResources=include
    )
    
    # Create Filter
    filter_obj = ib.Filter(
        Type=filter_type,
        Value=filter_value
    )
    
    if filter_unit is not None:
        filter_obj.Unit = filter_unit
    if retain_at_least is not None:
        filter_obj.RetainAtLeast = retain_at_least
    
    # Create PolicyDetail
    policy = ib.PolicyDetail(
        Action=action,
        Filter=filter_obj
    )
    
    # Verify structure
    assert policy.Action == action
    assert policy.Filter == filter_obj
    
    # Test serialization
    policy_dict = policy.to_dict()
    assert "Action" in policy_dict
    assert "Filter" in policy_dict


# Test Distribution with multiple regions

@given(
    regions=st.lists(st.text(min_size=1), min_size=1, max_size=5),
    ami_tags=st.dictionaries(st.text(min_size=1), st.text(), max_size=10),
    account_ids=st.lists(st.text(min_size=12, max_size=12).filter(str.isdigit), max_size=5)
)
def test_distribution_multi_region(regions, ami_tags, account_ids):
    """Test Distribution configuration across multiple regions"""
    distributions = []
    
    for region in regions:
        ami_config = ib.AmiDistributionConfiguration(
            AmiTags=ami_tags,
            TargetAccountIds=account_ids
        )
        
        dist = ib.Distribution(
            Region=region,
            AmiDistributionConfiguration=ami_config
        )
        distributions.append(dist)
    
    # Create DistributionConfiguration with multiple distributions
    dist_config = ib.DistributionConfiguration(
        "TestDistribution",
        Name="TestDist",
        Distributions=distributions
    )
    
    # Verify
    assert len(dist_config.Distributions) == len(regions)
    
    # Serialize
    config_dict = dist_config.to_dict()
    assert len(config_dict["Properties"]["Distributions"]) == len(regions)


# Test WorkflowConfiguration with parameters

@given(
    workflow_arn=st.text(min_size=1),
    on_failure=st.one_of(st.none(), st.sampled_from(["CONTINUE", "ABORT"])),
    parallel_group=st.one_of(st.none(), st.text()),
    param_names=st.lists(st.text(min_size=1), max_size=5),
    param_values=st.lists(st.lists(st.text(), min_size=1, max_size=3), max_size=5)
)
def test_workflow_configuration_params(workflow_arn, on_failure, parallel_group, param_names, param_values):
    """Test WorkflowConfiguration with parameters"""
    # Make sure we have matching param names and values
    assume(len(param_names) == len(param_values))
    
    # Create workflow parameters
    params = []
    for name, values in zip(param_names, param_values):
        param = ib.WorkflowParameter(Name=name, Value=values)
        params.append(param)
    
    # Create workflow configuration
    workflow = ib.WorkflowConfiguration(
        WorkflowArn=workflow_arn
    )
    
    if params:
        workflow.Parameters = params
    if on_failure is not None:
        workflow.OnFailure = on_failure
    if parallel_group is not None:
        workflow.ParallelGroup = parallel_group
    
    # Verify
    assert workflow.WorkflowArn == workflow_arn
    if params:
        assert workflow.Parameters == params
    
    # Test in Image
    image = ib.Image(
        "TestImage",
        Workflows=[workflow]
    )
    
    assert len(image.Workflows) == 1


# Test ImagePipeline with complete configuration

@given(
    name=st.text(min_size=1, max_size=100),
    description=st.one_of(st.none(), st.text(max_size=500)),
    status=st.one_of(st.none(), st.sampled_from(["ENABLED", "DISABLED"])),
    schedule_expr=st.one_of(st.none(), st.text()),
    test_enabled=st.one_of(st.none(), st.booleans()),
    timeout_minutes=st.one_of(st.none(), st.integers(min_value=1, max_value=1440))
)
def test_image_pipeline_complete(name, description, status, schedule_expr, test_enabled, timeout_minutes):
    """Test ImagePipeline with complete configuration"""
    # Create ImageTestsConfiguration
    if test_enabled is not None or timeout_minutes is not None:
        test_config = ib.ImageTestsConfiguration()
        if test_enabled is not None:
            test_config.ImageTestsEnabled = test_enabled
        if timeout_minutes is not None:
            test_config.TimeoutMinutes = timeout_minutes
    else:
        test_config = None
    
    # Create Schedule
    if schedule_expr is not None:
        schedule = ib.Schedule(ScheduleExpression=schedule_expr)
    else:
        schedule = None
    
    # Create ImagePipeline
    pipeline = ib.ImagePipeline(
        "TestPipeline",
        Name=name,
        InfrastructureConfigurationArn="arn:aws:imagebuilder:us-west-2:123456789012:infrastructure-configuration/test"
    )
    
    # Add optional properties
    if description is not None:
        pipeline.Description = description
    if status is not None:
        pipeline.Status = status
    if test_config is not None:
        pipeline.ImageTestsConfiguration = test_config
    if schedule is not None:
        pipeline.Schedule = schedule
    
    # Verify
    assert pipeline.Name == name
    if description is not None:
        assert pipeline.Description == description
    if status is not None:
        assert pipeline.Status == status
    
    # Serialize
    pipeline_dict = pipeline.to_dict()
    assert pipeline_dict["Properties"]["Name"] == name


# Test validation disabled

@given(
    name=st.text(),
    platform=st.text(),  # Any text, not just Linux/Windows
    version=st.text()
)
def test_component_no_validation(name, platform, version):
    """Test Component with validation disabled"""
    # Create component with validation disabled
    component = ib.Component(
        "TestComponent",
        Name=name,
        Platform=platform,  # Should accept any value with validation off
        Version=version,
        validation=False
    )
    
    # Should not validate platform value
    assert component.Name == name
    assert component.Platform == platform
    assert component.Version == version
    
    # to_dict with validation=False should work
    comp_dict = component.to_dict(validation=False)
    assert comp_dict["Properties"]["Platform"] == platform


# Test LifecyclePolicy with complex rules

@given(
    name=st.text(min_size=1),
    execution_role=st.text(min_size=1),
    resource_type=st.sampled_from(["AMI", "CONTAINER"]),
    policy_count=st.integers(min_value=1, max_value=5),
    status=st.one_of(st.none(), st.sampled_from(["ENABLED", "DISABLED"]))
)
def test_lifecycle_policy_complex(name, execution_role, resource_type, policy_count, status):
    """Test LifecyclePolicy with multiple policy details"""
    # Create multiple policy details
    policy_details = []
    for i in range(policy_count):
        action = ib.Action(Type=f"DELETE_{i}")
        filter_obj = ib.Filter(Type="AGE", Value=30 + i)
        policy_detail = ib.PolicyDetail(Action=action, Filter=filter_obj)
        policy_details.append(policy_detail)
    
    # Create resource selection
    resource_selection = ib.ResourceSelection()
    
    # Create lifecycle policy
    lifecycle = ib.LifecyclePolicy(
        "TestLifecycle",
        Name=name,
        ExecutionRole=execution_role,
        ResourceType=resource_type,
        PolicyDetails=policy_details,
        ResourceSelection=resource_selection
    )
    
    if status is not None:
        lifecycle.Status = status
    
    # Verify
    assert lifecycle.Name == name
    assert lifecycle.ExecutionRole == execution_role
    assert lifecycle.ResourceType == resource_type
    assert len(lifecycle.PolicyDetails) == policy_count
    
    # Serialize
    lifecycle_dict = lifecycle.to_dict()
    assert len(lifecycle_dict["Properties"]["PolicyDetails"]) == policy_count