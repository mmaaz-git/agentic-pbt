"""Property-based tests for troposphere.dax module using Hypothesis"""

import json
import math
from hypothesis import assume, given, strategies as st, settings
import pytest

# Import the modules to test
import troposphere.dax as dax
from troposphere.validators import boolean, integer


# Test 1: Boolean validator invariants
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_known_values(value):
    """Test that boolean validator correctly converts known values"""
    result = boolean(value)
    assert isinstance(result, bool)
    
    # Check expected conversions
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_values(value):
    """Test that boolean validator rejects invalid values"""
    # Skip valid values
    if value in [True, False, 1, 0, "1", "0", "true", "True", "false", "False"]:
        return
    
    with pytest.raises(ValueError):
        boolean(value)


# Test 2: Integer validator
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.strip() and (x.strip()[0] == '-' or x[0].isdigit()) and all(c.isdigit() for c in x.strip().lstrip('-')))
))  
def test_integer_validator_valid(value):
    """Test that integer validator accepts valid integers"""
    try:
        int(value)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        result = integer(value)
        assert result == value  # Should return the original value


@given(st.one_of(
    st.floats().filter(lambda x: not x.is_integer()),
    st.text().filter(lambda x: not x.strip() or not all(c.isdigit() or c == '-' for c in x.strip())),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator_invalid(value):
    """Test that integer validator rejects invalid values"""
    # Skip valid integers
    try:
        int(value)
        return  # Skip if it's actually a valid integer
    except (ValueError, TypeError):
        pass
    
    with pytest.raises(ValueError):
        integer(value)


# Test 3: Round-trip property for DAX objects
@given(
    cluster_name=st.text(min_size=1).filter(lambda x: x.isalnum()),
    iam_role=st.text(min_size=1),
    node_type=st.text(min_size=1),
    replication_factor=st.integers(min_value=1, max_value=10),
    description=st.text(),
    sse_enabled=st.booleans()
)
def test_cluster_to_dict_from_dict_roundtrip(cluster_name, iam_role, node_type, 
                                              replication_factor, description, 
                                              sse_enabled):
    """Test that Cluster objects survive to_dict/from_dict round-trip"""
    # Create a cluster with various properties
    original = dax.Cluster(
        "MyCluster",
        ClusterName=cluster_name,
        IAMRoleARN=iam_role,
        NodeType=node_type,
        ReplicationFactor=replication_factor,
        Description=description,
        SSESpecification=dax.SSESpecification(SSEEnabled=sse_enabled)
    )
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = dax.Cluster.from_dict("MyCluster", dict_repr["Properties"])
    
    # They should be equal
    assert original == reconstructed
    assert original.to_json(validation=False) == reconstructed.to_json(validation=False)


# Test 4: Title validation  
@given(st.text())
def test_title_validation(title):
    """Test that only alphanumeric titles are accepted"""
    is_valid = bool(title and title.isalnum())
    
    if is_valid:
        # Should create successfully
        obj = dax.Cluster(
            title,
            IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
            NodeType="dax.r3.large",
            ReplicationFactor=1
        )
        assert obj.title == title
    else:
        # Should raise ValueError for invalid titles
        with pytest.raises(ValueError) as exc_info:
            dax.Cluster(
                title,
                IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
                NodeType="dax.r3.large",
                ReplicationFactor=1
            )
        assert 'not alphanumeric' in str(exc_info.value)


# Test 5: Required properties validation
@given(
    include_iam_role=st.booleans(),
    include_node_type=st.booleans(),
    include_replication_factor=st.booleans()
)
def test_required_properties_validation(include_iam_role, include_node_type, 
                                        include_replication_factor):
    """Test that missing required properties raise errors"""
    kwargs = {}
    
    if include_iam_role:
        kwargs["IAMRoleARN"] = "arn:aws:iam::123456789012:role/DAXRole"
    if include_node_type:
        kwargs["NodeType"] = "dax.r3.large" 
    if include_replication_factor:
        kwargs["ReplicationFactor"] = 1
    
    # All three properties are required
    all_present = include_iam_role and include_node_type and include_replication_factor
    
    if all_present:
        # Should succeed
        cluster = dax.Cluster("TestCluster", **kwargs)
        cluster.to_dict()  # Validation happens here
    else:
        # Should fail validation
        cluster = dax.Cluster("TestCluster", **kwargs)
        with pytest.raises(ValueError) as exc_info:
            cluster.to_dict()
        assert "required" in str(exc_info.value).lower()


# Test 6: Type validation in properties
@given(
    replication_factor=st.one_of(
        st.integers(),
        st.text(),
        st.floats(),
        st.lists(st.integers()),
        st.none()
    )
)
def test_replication_factor_type_validation(replication_factor):
    """Test that ReplicationFactor validates integer type"""
    # Check if the value can be converted to int
    try:
        int(replication_factor)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        # Should succeed
        cluster = dax.Cluster(
            "TestCluster",
            IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
            NodeType="dax.r3.large",
            ReplicationFactor=replication_factor
        )
        assert cluster.ReplicationFactor == replication_factor
    else:
        # Should fail with validation error
        with pytest.raises((ValueError, TypeError)):
            cluster = dax.Cluster(
                "TestCluster",
                IAMRoleARN="arn:aws:iam::123456789012:role/DAXRole",
                NodeType="dax.r3.large",
                ReplicationFactor=replication_factor
            )


# Test 7: SSESpecification boolean property
@given(sse_value=st.one_of(
    st.booleans(),
    st.sampled_from([0, 1, "0", "1", "true", "false", "True", "False"]),
    st.text(),
    st.integers(),
    st.none()
))
def test_sse_specification_boolean_property(sse_value):
    """Test that SSEEnabled property uses boolean validator"""
    # Check if it's a valid boolean value
    is_valid = sse_value in [True, False, 0, 1, "0", "1", "true", "false", "True", "False"]
    
    if is_valid:
        # Should succeed
        sse_spec = dax.SSESpecification(SSEEnabled=sse_value)
        # The value should be converted to boolean
        assert isinstance(sse_spec.SSEEnabled, bool)
        
        # Check expected conversion
        if sse_value in [True, 1, "1", "true", "True"]:
            assert sse_spec.SSEEnabled is True
        elif sse_value in [False, 0, "0", "false", "False"]:
            assert sse_spec.SSEEnabled is False
    else:
        # Should fail validation
        with pytest.raises((ValueError, TypeError)):
            dax.SSESpecification(SSEEnabled=sse_value)


if __name__ == "__main__":
    # Run a quick test to make sure imports work
    print("Testing troposphere.dax module...")
    test_boolean_validator_known_values()
    test_cluster_to_dict_from_dict_roundtrip()
    print("Basic tests passed!")