#!/usr/bin/env python3
"""Property-based tests for troposphere.managedblockchain module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import managedblockchain
from troposphere import Tags, Template


# Strategies for generating valid field values
text_strategy = st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126))
integer_strategy = st.integers(min_value=0, max_value=1000000)
tag_strategy = st.dictionaries(
    keys=text_strategy,
    values=text_strategy,
    min_size=0,
    max_size=5
)


# Test 1: Required field validation
@given(
    admin_username=text_strategy,
    admin_password=text_strategy,
    include_username=st.booleans(),
    include_password=st.booleans()
)
def test_member_fabric_configuration_required_fields(admin_username, admin_password, include_username, include_password):
    """Test that MemberFabricConfiguration validates required fields."""
    
    kwargs = {}
    if include_username:
        kwargs['AdminUsername'] = admin_username
    if include_password:
        kwargs['AdminPassword'] = admin_password
    
    if include_username and include_password:
        # Should succeed with both required fields
        config = managedblockchain.MemberFabricConfiguration(**kwargs)
        assert config.AdminUsername == admin_username
        assert config.AdminPassword == admin_password
    else:
        # Should fail without required fields
        with pytest.raises(ValueError, match="required"):
            config = managedblockchain.MemberFabricConfiguration(**kwargs)
            config._validate_props()


# Test 2: Round-trip property for Accessor
@given(
    accessor_type=text_strategy,
    network_type=st.one_of(st.none(), text_strategy),
    tags=st.one_of(st.none(), tag_strategy)
)
def test_accessor_round_trip(accessor_type, network_type, tags):
    """Test that Accessor objects can be converted to dict and back."""
    
    kwargs = {'AccessorType': accessor_type}
    if network_type is not None:
        kwargs['NetworkType'] = network_type
    if tags is not None:
        kwargs['Tags'] = Tags(tags)
    
    # Create accessor with a title
    original = managedblockchain.Accessor('TestAccessor', **kwargs)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Create new object from dict
    reconstructed = managedblockchain.Accessor.from_dict('TestAccessor', dict_repr)
    
    # They should be equal
    assert original == reconstructed
    assert original.to_dict() == reconstructed.to_dict()


# Test 3: Equality property
@given(
    name1=text_strategy,
    name2=text_strategy,
    description=st.one_of(st.none(), text_strategy)
)
def test_member_configuration_equality(name1, name2, description):
    """Test equality of MemberConfiguration objects."""
    
    kwargs1 = {'Name': name1}
    kwargs2 = {'Name': name2}
    
    if description is not None:
        kwargs1['Description'] = description
        kwargs2['Description'] = description
    
    config1 = managedblockchain.MemberConfiguration(**kwargs1)
    config2 = managedblockchain.MemberConfiguration(**kwargs2)
    config1_copy = managedblockchain.MemberConfiguration(**kwargs1)
    
    # Reflexivity
    assert config1 == config1
    
    # Same data should be equal
    assert config1 == config1_copy
    assert config1_copy == config1  # Symmetry
    
    # Different data should not be equal
    if name1 != name2:
        assert config1 != config2


# Test 4: Integer field validation with ApprovalThresholdPolicy
@given(
    proposal_duration=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none()
    ),
    threshold_percentage=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.none()
    ),
    threshold_comparator=st.one_of(st.none(), text_strategy)
)
def test_approval_threshold_policy_integer_validation(proposal_duration, threshold_percentage, threshold_comparator):
    """Test that ApprovalThresholdPolicy properly validates integer fields."""
    
    kwargs = {}
    
    # Add fields if they should be convertible to int
    if proposal_duration is not None:
        try:
            int(proposal_duration)
            kwargs['ProposalDurationInHours'] = proposal_duration
            valid_duration = True
        except (ValueError, TypeError):
            valid_duration = False
    else:
        valid_duration = True
        
    if threshold_percentage is not None:
        try:
            int(threshold_percentage)
            kwargs['ThresholdPercentage'] = threshold_percentage
            valid_percentage = True
        except (ValueError, TypeError):
            valid_percentage = False
    else:
        valid_percentage = True
    
    if threshold_comparator is not None:
        kwargs['ThresholdComparator'] = threshold_comparator
    
    # If we provided invalid integers, expect validation to fail
    if (proposal_duration is not None and not valid_duration) or \
       (threshold_percentage is not None and not valid_percentage):
        with pytest.raises(ValueError):
            policy = managedblockchain.ApprovalThresholdPolicy(**kwargs)
    else:
        # Should succeed with valid or missing optional fields
        policy = managedblockchain.ApprovalThresholdPolicy(**kwargs)
        # Verify the values were stored
        if proposal_duration is not None:
            assert policy.ProposalDurationInHours == proposal_duration
        if threshold_percentage is not None:
            assert policy.ThresholdPercentage == threshold_percentage


# Test 5: Complex nested structure round-trip
@given(
    member_name=text_strategy,
    member_desc=st.one_of(st.none(), text_strategy),
    admin_username=text_strategy,
    admin_password=text_strategy,
    network_name=text_strategy,
    network_desc=st.one_of(st.none(), text_strategy),
    framework=text_strategy,
    framework_version=text_strategy,
    edition=text_strategy,
    proposal_duration=integer_strategy,
    threshold_percentage=st.integers(min_value=0, max_value=100),
    threshold_comparator=st.sampled_from(['GREATER_THAN', 'GREATER_THAN_OR_EQUAL_TO'])
)
@settings(max_examples=100)
def test_member_complex_round_trip(
    member_name, member_desc, admin_username, admin_password,
    network_name, network_desc, framework, framework_version, edition,
    proposal_duration, threshold_percentage, threshold_comparator
):
    """Test round-trip property for complex nested Member structure."""
    
    # Build nested structure
    fabric_config = managedblockchain.MemberFabricConfiguration(
        AdminUsername=admin_username,
        AdminPassword=admin_password
    )
    
    member_framework_config = managedblockchain.MemberFrameworkConfiguration(
        MemberFabricConfiguration=fabric_config
    )
    
    member_config_kwargs = {'Name': member_name}
    if member_desc:
        member_config_kwargs['Description'] = member_desc
    member_config_kwargs['MemberFrameworkConfiguration'] = member_framework_config
    
    member_config = managedblockchain.MemberConfiguration(**member_config_kwargs)
    
    # Network configuration
    network_fabric_config = managedblockchain.NetworkFabricConfiguration(
        Edition=edition
    )
    
    network_framework_config = managedblockchain.NetworkFrameworkConfiguration(
        NetworkFabricConfiguration=network_fabric_config
    )
    
    approval_policy = managedblockchain.ApprovalThresholdPolicy(
        ProposalDurationInHours=proposal_duration,
        ThresholdPercentage=threshold_percentage,
        ThresholdComparator=threshold_comparator
    )
    
    voting_policy = managedblockchain.VotingPolicy(
        ApprovalThresholdPolicy=approval_policy
    )
    
    network_config_kwargs = {
        'Framework': framework,
        'FrameworkVersion': framework_version,
        'Name': network_name,
        'VotingPolicy': voting_policy,
        'NetworkFrameworkConfiguration': network_framework_config
    }
    if network_desc:
        network_config_kwargs['Description'] = network_desc
        
    network_config = managedblockchain.NetworkConfiguration(**network_config_kwargs)
    
    # Create Member
    member = managedblockchain.Member(
        'TestMember',
        MemberConfiguration=member_config,
        NetworkConfiguration=network_config
    )
    
    # Round-trip test
    dict_repr = member.to_dict()
    reconstructed = managedblockchain.Member.from_dict('TestMember', dict_repr)
    
    assert member == reconstructed
    assert member.to_dict() == reconstructed.to_dict()


# Test 6: Node configuration validation
@given(
    availability_zone=text_strategy,
    instance_type=text_strategy,
    include_az=st.booleans(),
    include_instance=st.booleans()
)
def test_node_configuration_required_fields(availability_zone, instance_type, include_az, include_instance):
    """Test that NodeConfiguration validates its required fields."""
    
    kwargs = {}
    if include_az:
        kwargs['AvailabilityZone'] = availability_zone
    if include_instance:
        kwargs['InstanceType'] = instance_type
    
    if include_az and include_instance:
        # Should succeed with both required fields
        config = managedblockchain.NodeConfiguration(**kwargs)
        assert config.AvailabilityZone == availability_zone
        assert config.InstanceType == instance_type
    else:
        # Should fail without required fields
        with pytest.raises(ValueError, match="required"):
            config = managedblockchain.NodeConfiguration(**kwargs)
            config._validate_props()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])