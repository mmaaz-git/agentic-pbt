#!/usr/bin/env python3
"""Property-based tests for troposphere.msk module"""

import sys
import json
from hypothesis import given, strategies as st, settings, assume
import pytest

# Add the venv to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.msk as msk
from troposphere import AWSObject, AWSProperty
from troposphere.validators import boolean, integer


# Strategy for valid boolean inputs
bool_strategy = st.sampled_from([
    True, False, 
    1, 0,
    "true", "false", 
    "True", "False",
    "1", "0"
])

# Strategy for invalid boolean inputs
invalid_bool_strategy = st.one_of(
    st.text().filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
)

# Property 1: boolean validator round-trip
@given(bool_strategy)
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator correctly handles all valid inputs"""
    result = boolean(value)
    assert isinstance(result, bool)
    # Check that the conversion is consistent
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


# Property 2: boolean validator rejects invalid inputs  
@given(invalid_bool_strategy)
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs"""
    with pytest.raises(ValueError):
        boolean(value)


# Property 3: integer validator accepts valid integers
@given(st.one_of(
    st.integers(),
    st.text().map(str).filter(lambda x: x.lstrip('-').isdigit())
))
def test_integer_validator_valid(value):
    """Test that integer validator accepts valid integer representations"""
    try:
        result = integer(value)
        # Should be convertible to int
        int(result)
    except ValueError:
        # Only string representations of numbers should work
        if isinstance(value, str):
            assert not value.lstrip('-').isdigit()


# Property 4: Required properties validation
@given(
    cluster_name=st.text(min_size=1, max_size=100),
    kafka_version=st.text(min_size=1, max_size=20),
    num_brokers=st.integers(min_value=1, max_value=15)
)
def test_cluster_required_properties(cluster_name, kafka_version, num_brokers):
    """Test that Cluster enforces required properties"""
    # Should fail without required props
    with pytest.raises(ValueError):
        cluster = msk.Cluster("TestCluster")
        cluster.to_dict()
    
    # Should succeed with all required props
    broker_info = msk.BrokerNodeGroupInfo(
        ClientSubnets=["subnet-1", "subnet-2"],
        InstanceType="kafka.m5.large"
    )
    
    cluster = msk.Cluster(
        "TestCluster",
        ClusterName=cluster_name,
        KafkaVersion=kafka_version,
        NumberOfBrokerNodes=num_brokers,
        BrokerNodeGroupInfo=broker_info
    )
    
    # Should serialize without error
    result = cluster.to_dict()
    assert result["Type"] == "AWS::MSK::Cluster"
    assert result["Properties"]["ClusterName"] == cluster_name


# Property 5: to_dict/from_dict round-trip
@given(
    enabled=bool_strategy
)
def test_iam_round_trip(enabled):
    """Test that Iam property can round-trip through dict serialization"""
    original = msk.Iam(Enabled=boolean(enabled))
    
    # Convert to dict
    d = original.to_dict()
    
    # Create new object from dict
    reconstructed = msk.Iam._from_dict(**d)
    
    # Should be equivalent
    assert original.to_dict() == reconstructed.to_dict()


# Property 6: Nested property validation
@given(
    vpc_enabled=bool_strategy,
    scram_enabled=bool_strategy
)
def test_nested_property_structure(vpc_enabled, scram_enabled):
    """Test that nested properties maintain correct structure"""
    vpc_scram = msk.VpcConnectivityScram(Enabled=boolean(scram_enabled))
    vpc_sasl = msk.VpcConnectivitySasl(Scram=vpc_scram)
    vpc_auth = msk.VpcConnectivityClientAuthentication(Sasl=vpc_sasl)
    vpc_conn = msk.VpcConnectivity(ClientAuthentication=vpc_auth)
    
    d = vpc_conn.to_dict()
    
    # Check nested structure is preserved
    assert "ClientAuthentication" in d
    assert "Sasl" in d["ClientAuthentication"]
    assert "Scram" in d["ClientAuthentication"]["Sasl"]
    assert "Enabled" in d["ClientAuthentication"]["Sasl"]["Scram"]


# Property 7: Property type enforcement
@given(
    invalid_value=st.one_of(
        st.text(),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)  
def test_integer_property_type_enforcement(invalid_value):
    """Test that integer properties reject non-integer values"""
    assume(not isinstance(invalid_value, str) or not invalid_value.lstrip('-').isdigit())
    
    with pytest.raises((TypeError, ValueError)):
        config = msk.ConfigurationInfo(
            Arn="arn:aws:kafka:us-east-1:123456789012:configuration/test",
            Revision=invalid_value  # Should be integer
        )
        config.to_dict()


# Property 8: Tags property accepts dict
@given(
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_cluster_tags_property(tags):
    """Test that Cluster accepts tags as dict"""
    broker_info = msk.BrokerNodeGroupInfo(
        ClientSubnets=["subnet-1"],
        InstanceType="kafka.m5.large"
    )
    
    cluster = msk.Cluster(
        "TestCluster",
        ClusterName="test",
        KafkaVersion="2.8.0", 
        NumberOfBrokerNodes=3,
        BrokerNodeGroupInfo=broker_info,
        Tags=tags
    )
    
    d = cluster.to_dict()
    if tags:
        assert d["Properties"]["Tags"] == tags
    else:
        # Empty tags might be omitted or included
        assert "Tags" not in d["Properties"] or d["Properties"]["Tags"] == {}


# Property 9: List properties validation
@given(
    subnet_ids=st.lists(
        st.text(min_size=1, max_size=50),
        min_size=1,  # At least one required
        max_size=10
    )
)
def test_list_property_validation(subnet_ids):
    """Test that list properties are properly validated"""
    broker_info = msk.BrokerNodeGroupInfo(
        ClientSubnets=subnet_ids,
        InstanceType="kafka.m5.large"
    )
    
    d = broker_info.to_dict()
    assert d["ClientSubnets"] == subnet_ids
    assert isinstance(d["ClientSubnets"], list)


# Property 10: Optional vs required property handling
@given(
    include_optional=st.booleans()
)
def test_optional_property_handling(include_optional):
    """Test that optional properties can be omitted"""
    props = {
        "Enabled": True
    }
    
    if include_optional:
        props["LogGroup"] = "/aws/msk/test"
    
    logs = msk.CloudWatchLogs(**props)
    d = logs.to_dict()
    
    assert d["Enabled"] is True
    if include_optional:
        assert d["LogGroup"] == "/aws/msk/test"
    else:
        assert "LogGroup" not in d


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])