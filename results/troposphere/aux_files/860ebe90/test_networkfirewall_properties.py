#!/usr/bin/env python3
"""Property-based tests for troposphere.networkfirewall module"""

import sys
import os

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere import networkfirewall
from troposphere.validators.networkfirewall import validate_rule_group_type


# Test 1: validate_rule_group_type validator consistency
@given(st.text())
def test_validate_rule_group_type_only_accepts_valid_types(rule_type):
    """Test that validate_rule_group_type only accepts STATEFUL or STATELESS"""
    if rule_type in ("STATEFUL", "STATELESS"):
        # Should not raise for valid types
        result = validate_rule_group_type(rule_type)
        assert result == rule_type
    else:
        # Should raise ValueError for invalid types
        with pytest.raises(ValueError) as exc_info:
            validate_rule_group_type(rule_type)
        assert "RuleGroup Type must be one of" in str(exc_info.value)


# Test 2: PortRange property - test integers are validated
@given(
    from_port=st.one_of(st.integers(), st.text(), st.floats(), st.none()),
    to_port=st.one_of(st.integers(), st.text(), st.floats(), st.none())
)
def test_portrange_type_validation(from_port, to_port):
    """Test that PortRange validates integer types for ports"""
    try:
        port_range = networkfirewall.PortRange(
            FromPort=from_port,
            ToPort=to_port
        )
        # If it succeeds, validate the types are integers
        assert isinstance(port_range.properties.get('FromPort'), (int, type(None)))
        assert isinstance(port_range.properties.get('ToPort'), (int, type(None)))
    except (TypeError, AttributeError, ValueError):
        # Should fail for non-integer types
        if not (isinstance(from_port, int) and isinstance(to_port, int)):
            pass  # Expected failure for non-integer types
        else:
            raise  # Unexpected failure for integer types


# Test 3: Required properties enforcement 
@given(
    subnet_id=st.one_of(st.text(), st.none()),
    ip_address_type=st.one_of(st.text(), st.none())
)
def test_subnetmapping_required_properties(subnet_id, ip_address_type):
    """Test that SubnetMapping enforces required SubnetId property"""
    kwargs = {}
    if subnet_id is not None:
        kwargs['SubnetId'] = subnet_id
    if ip_address_type is not None:
        kwargs['IPAddressType'] = ip_address_type
    
    if subnet_id is None:
        # Should fail when required property is missing during validation
        subnet_mapping = networkfirewall.SubnetMapping(**kwargs)
        with pytest.raises(ValueError) as exc_info:
            subnet_mapping.to_dict()  # This triggers validation
        assert "required" in str(exc_info.value).lower()
    else:
        # Should succeed when required property is present
        subnet_mapping = networkfirewall.SubnetMapping(**kwargs)
        result = subnet_mapping.to_dict()
        assert 'SubnetId' in result
        assert result['SubnetId'] == subnet_id


# Test 4: RuleGroup Type property validation
@given(
    capacity=st.integers(),
    rule_group_name=st.text(min_size=1),
    rule_type=st.text()
)
def test_rulegroup_type_validation(capacity, rule_group_name, rule_type):
    """Test that RuleGroup validates its Type property"""
    try:
        rule_group = networkfirewall.RuleGroup(
            Capacity=capacity,
            RuleGroupName=rule_group_name,
            Type=rule_type
        )
        # If creation succeeds, to_dict should also succeed only for valid types
        result = rule_group.to_dict()
        assert rule_type in ("STATEFUL", "STATELESS")
    except (ValueError, TypeError) as e:
        # Should fail for invalid rule types
        if rule_type not in ("STATEFUL", "STATELESS"):
            pass  # Expected failure
        else:
            raise  # Unexpected failure for valid types


# Test 5: Address property structure
@given(address_def=st.text())
def test_address_required_property(address_def):
    """Test that Address enforces AddressDefinition as required"""
    address = networkfirewall.Address(AddressDefinition=address_def)
    result = address.to_dict()
    assert 'AddressDefinition' in result
    assert result['AddressDefinition'] == address_def


# Test 6: CustomAction structure validation
@given(
    action_name=st.text(min_size=1)
)
def test_customaction_requires_actiondefinition(action_name):
    """Test that CustomAction requires both ActionName and ActionDefinition"""
    # Create a valid ActionDefinition first
    publish_metric = networkfirewall.PublishMetricAction(
        Dimensions=[networkfirewall.Dimension(Value="test")]
    )
    action_def = networkfirewall.ActionDefinition(
        PublishMetricAction=publish_metric
    )
    
    # CustomAction should work with both required properties
    custom_action = networkfirewall.CustomAction(
        ActionName=action_name,
        ActionDefinition=action_def
    )
    result = custom_action.to_dict()
    assert 'ActionName' in result
    assert 'ActionDefinition' in result


# Test 7: List properties validation
@given(
    definitions=st.lists(st.text())
)
def test_ipset_definition_list_property(definitions):
    """Test that IPSet correctly handles list properties"""
    ipset = networkfirewall.IPSet(Definition=definitions)
    result = ipset.to_dict()
    if definitions:  # Only check if not empty
        assert 'Definition' in result
        assert result['Definition'] == definitions
        assert isinstance(result['Definition'], list)


# Test 8: Integer validation for Capacity
@given(
    capacity=st.one_of(
        st.integers(min_value=-1000, max_value=1000000),
        st.text(),
        st.floats(),
        st.none()
    )
)
def test_rulegroup_capacity_integer_validation(capacity):
    """Test that RuleGroup validates Capacity as integer"""
    if not isinstance(capacity, int):
        with pytest.raises((TypeError, ValueError, AttributeError)):
            networkfirewall.RuleGroup(
                Capacity=capacity,
                RuleGroupName="test",
                Type="STATEFUL"
            )
    else:
        rule_group = networkfirewall.RuleGroup(
            Capacity=capacity,
            RuleGroupName="test", 
            Type="STATEFUL"
        )
        result = rule_group.to_dict()
        assert result['Properties']['Capacity'] == capacity


if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])