#!/usr/bin/env python3
"""Property-based tests for troposphere.elasticache module"""

import re
from hypothesis import given, assume, strategies as st, settings
import troposphere.elasticache as elasticache
from troposphere.validators.elasticache import (
    validate_node_group_id,
    validate_network_port,
    validate_cache_cluster,
    validate_replication_group,
)


# Test 1: validate_node_group_id regex property
@given(st.text())
def test_validate_node_group_id_accepts_only_valid_pattern(node_id):
    """Test that validate_node_group_id accepts only strings matching \\d{1,4}"""
    try:
        result = validate_node_group_id(node_id)
        # If validation passes, check if it actually matches the pattern
        assert re.match(r"^\d{1,4}$", result), f"Accepted invalid node_id: {node_id}"
    except ValueError:
        # If validation fails, ensure the input doesn't match the pattern
        assert not re.match(r"^\d{1,4}$", node_id), f"Rejected valid node_id: {node_id}"


@given(st.integers(min_value=0, max_value=9999))
def test_validate_node_group_id_accepts_valid_numeric_strings(num):
    """Test that valid numeric strings (1-4 digits) are accepted"""
    node_id = str(num)
    result = validate_node_group_id(node_id)
    assert result == node_id


@given(st.text(min_size=1))
def test_validate_node_group_id_regex_correctness(text):
    """Test if the regex in validate_node_group_id correctly matches what it claims"""
    # The function uses r"\\d{1,4}" which should match 1-4 digits
    # But it's not anchored, so it might match strings with extra characters
    if re.match(r"\\d{1,4}", text):
        # If Python's regex matches, the function should accept it
        try:
            result = validate_node_group_id(text)
            # Check if result is what we expect
            assert result == text
        except ValueError as e:
            # This would be a bug - regex matched but function rejected
            assert False, f"Regex matched but function rejected: {text}"


# Test 2: validate_network_port range property
@given(st.integers())
def test_validate_network_port_range(port):
    """Test that network ports are correctly validated in range [-1, 65535]"""
    try:
        result = validate_network_port(port)
        # If validation passes, port should be in valid range
        assert -1 <= port <= 65535, f"Accepted out-of-range port: {port}"
        assert result == port
    except ValueError as e:
        # If validation fails, port should be out of range
        assert port < -1 or port > 65535, f"Rejected valid port: {port}"


@given(st.integers(min_value=-1, max_value=65535))
def test_validate_network_port_accepts_valid_range(port):
    """Test that all ports in valid range are accepted"""
    result = validate_network_port(port)
    assert result == port


# Test 3: validate_cache_cluster AZMode property
@given(
    preferred_azs=st.one_of(
        st.none(),
        st.lists(st.text(min_size=1), min_size=0, max_size=5)
    ),
    az_mode=st.one_of(
        st.none(),
        st.sampled_from(["single-az", "cross-az", "invalid-mode"])
    )
)
def test_validate_cache_cluster_az_mode_property(preferred_azs, az_mode):
    """Test AZMode validation when multiple AZs are specified"""
    
    # Create a mock CacheCluster object
    cluster = elasticache.CacheCluster(
        "TestCluster",
        CacheNodeType="cache.t3.micro",
        Engine="redis",
        NumCacheNodes=1
    )
    
    # Set properties if provided
    if preferred_azs is not None:
        cluster.properties["PreferredAvailabilityZones"] = preferred_azs
    if az_mode is not None:
        cluster.properties["AZMode"] = az_mode
    
    # Test the validation
    try:
        validate_cache_cluster(cluster)
        # If validation passes, check the constraint
        if preferred_azs and len(preferred_azs) > 1:
            # Multiple AZs specified - AZMode must be "cross-az" or not set
            if az_mode is not None and az_mode != "cross-az":
                assert False, f"Should have failed: multiple AZs with AZMode={az_mode}"
    except ValueError as e:
        # If validation fails, it should be because of the AZMode constraint
        assert preferred_azs and len(preferred_azs) > 1, "Failed for wrong reason"
        assert az_mode is not None and az_mode != "cross-az", "Failed incorrectly"


# Test 4: validate_replication_group required fields property
@given(
    has_num_cache=st.booleans(),
    has_num_groups=st.booleans(),
    has_replicas=st.booleans(),
    has_primary=st.booleans()
)
def test_validate_replication_group_required_fields(
    has_num_cache, has_num_groups, has_replicas, has_primary
):
    """Test that at least one required field must be present"""
    
    # Create a ReplicationGroup with required field
    group = elasticache.ReplicationGroup(
        "TestGroup",
        ReplicationGroupDescription="Test Description"
    )
    
    # Add optional fields based on flags
    if has_num_cache:
        group.properties["NumCacheClusters"] = 2
    if has_num_groups:
        group.properties["NumNodeGroups"] = 1
    if has_replicas:
        group.properties["ReplicasPerNodeGroup"] = 1
    if has_primary:
        group.properties["PrimaryClusterId"] = "primary-cluster"
    
    # Test validation
    has_any_required = has_num_cache or has_num_groups or has_replicas or has_primary
    
    try:
        validate_replication_group(group)
        # Should only pass if at least one required field is present
        assert has_any_required, "Validation passed without required fields"
    except ValueError as e:
        # Should only fail if no required fields are present
        assert not has_any_required, "Validation failed with required fields present"


# Additional edge case tests for node_group_id
@given(st.text())
def test_node_group_id_partial_match_bug(text):
    """Test if validate_node_group_id has a partial match bug"""
    # The regex r"\\d{1,4}" without anchors will match "12345" as "1234"
    # Let's test strings that contain 1-4 digits but have extra characters
    if re.search(r"\\d{1,4}", text) and not re.match(r"^\\d{1,4}$", text):
        # Contains 1-4 digits somewhere but isn't exactly 1-4 digits
        try:
            result = validate_node_group_id(text)
            # If this passes, it's a bug - the function should only accept exact matches
            # But the regex isn't anchored, so it might accept partial matches
            assert re.match(r"^\\d{1,4}$", result), f"Accepted string with extra chars: {text}"
        except ValueError:
            # This is expected for strings with extra characters
            pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])