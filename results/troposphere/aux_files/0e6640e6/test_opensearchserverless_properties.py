#!/usr/bin/env python3
"""Property-based tests for troposphere.opensearchserverless module."""

import json
import sys
import os
from hypothesis import assume, given, strategies as st, settings
import pytest

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.opensearchserverless as oss
from troposphere import validators


# Test 1: Boolean validator property - accepts specific values and preserves boolean logic
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator correctly handles valid inputs."""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    
    # Test invariant: values that convert to True/False remain consistent
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(st.text(), st.integers(), st.floats(), st.none()))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs."""
    # Skip valid values
    assume(value not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"])
    
    with pytest.raises(ValueError):
        validators.boolean(value)


# Test 2: Integer validator property - preserves integer conversion
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.strip() and (x.strip().lstrip('-').isdigit())),
))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer inputs."""
    try:
        int(value)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        result = validators.integer(value)
        # Property: validator should preserve the ability to convert to int
        assert int(result) == int(value)


@given(st.integers(min_value=-1000000, max_value=1000000))
def test_integer_validator_integer_invariant(value):
    """Test that integer validator preserves integer values."""
    result = validators.integer(value)
    assert int(result) == value


# Test 3: AccessPolicy required properties validation
@given(
    name=st.text(min_size=1, max_size=50),
    policy=st.text(min_size=1, max_size=100),
    policy_type=st.sampled_from(["data", "encryption", "network"])
)
def test_access_policy_required_properties(name, policy, policy_type):
    """Test that AccessPolicy enforces required properties."""
    # Create with all required properties
    ap = oss.AccessPolicy(
        title="TestPolicy",
        Name=name,
        Policy=policy,
        Type=policy_type
    )
    
    # Should convert to dict without error
    d = ap.to_dict()
    assert d["Properties"]["Name"] == name
    assert d["Properties"]["Policy"] == policy
    assert d["Properties"]["Type"] == policy_type


@given(
    name=st.text(min_size=1, max_size=50),
    policy=st.text(min_size=1, max_size=100)
)
def test_access_policy_missing_required_property(name, policy):
    """Test that AccessPolicy raises error when required property is missing."""
    ap = oss.AccessPolicy(
        title="TestPolicy",
        Name=name,
        Policy=policy
        # Missing required Type property
    )
    
    # Should raise ValueError when validating
    with pytest.raises(ValueError, match="Resource Type required"):
        ap.to_dict()


# Test 4: Collection round-trip property
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    description=st.text(max_size=100),
    collection_type=st.sampled_from(["SEARCH", "TIMESERIES", "VECTORSEARCH"])
)
def test_collection_round_trip(name, description, collection_type):
    """Test that Collection can round-trip through to_dict/from_dict."""
    # Create original collection
    original = oss.Collection(
        title="TestCollection",
        Name=name,
        Description=description,
        Type=collection_type
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Extract properties (remove Type field which is resource type)
    props = dict_repr.get("Properties", {})
    
    # Create new collection from dict
    reconstructed = oss.Collection.from_dict("TestCollection", props)
    
    # Check that properties match
    assert reconstructed.Name == original.Name
    assert reconstructed.Description == original.Description
    assert reconstructed.Type == original.Type


# Test 5: Index Settings validation
@given(
    knn_enabled=st.booleans(),
    ef_search=st.integers(min_value=1, max_value=2000),
    refresh_interval=st.sampled_from(["1s", "5s", "10s", "30s", "60s"])
)
def test_index_settings_property_types(knn_enabled, ef_search, refresh_interval):
    """Test that Index Settings enforces correct property types."""
    index_prop = oss.IndexProperty(
        Knn=knn_enabled,
        KnnAlgoParamEfSearch=ef_search,
        RefreshInterval=refresh_interval
    )
    
    settings = oss.IndexSettings(
        Index=index_prop
    )
    
    # Create an Index with these settings
    index = oss.Index(
        title="TestIndex",
        CollectionEndpoint="https://test.opensearch.example.com",
        IndexName="test-index",
        Settings=settings
    )
    
    # Should convert to dict successfully
    d = index.to_dict()
    assert d["Properties"]["Settings"]["Index"]["Knn"] == knn_enabled
    assert d["Properties"]["Settings"]["Index"]["KnnAlgoParamEfSearch"] == ef_search
    assert d["Properties"]["Settings"]["Index"]["RefreshInterval"] == refresh_interval


# Test 6: VpcEndpoint subnet validation
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    vpc_id=st.text(min_size=1, max_size=50),
    subnet_ids=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10)
)
def test_vpc_endpoint_required_subnets(name, vpc_id, subnet_ids):
    """Test that VpcEndpoint requires SubnetIds list."""
    vpc = oss.VpcEndpoint(
        title="TestVPC",
        Name=name,
        VpcId=vpc_id,
        SubnetIds=subnet_ids
    )
    
    d = vpc.to_dict()
    assert d["Properties"]["SubnetIds"] == subnet_ids
    assert len(d["Properties"]["SubnetIds"]) >= 1


# Test 7: Title validation for alphanumeric constraint
@given(st.text(min_size=1))
def test_title_validation_alphanumeric(title):
    """Test that resource titles must be alphanumeric."""
    is_alphanumeric = title.isalnum()
    
    try:
        ap = oss.AccessPolicy(
            title=title,
            Name="test",
            Policy="{}",
            Type="data"
        )
        # If we got here, title was accepted
        assert is_alphanumeric, f"Non-alphanumeric title '{title}' was incorrectly accepted"
    except ValueError as e:
        # Title was rejected
        assert not is_alphanumeric, f"Alphanumeric title '{title}' was incorrectly rejected"
        assert "not alphanumeric" in str(e)


# Test 8: SecurityConfig SAML options validation
@given(
    metadata=st.text(min_size=1, max_size=1000),
    session_timeout=st.integers(min_value=1, max_value=720)
)
def test_security_config_saml_timeout(metadata, session_timeout):
    """Test that SecurityConfig correctly handles SAML session timeout as integer."""
    saml_options = oss.SamlConfigOptions(
        Metadata=metadata,
        SessionTimeout=session_timeout
    )
    
    config = oss.SecurityConfig(
        title="TestSecConfig",
        SamlOptions=saml_options
    )
    
    d = config.to_dict()
    # Property: SessionTimeout should preserve integer value
    assert d["Properties"]["SamlOptions"]["SessionTimeout"] == session_timeout
    assert isinstance(d["Properties"]["SamlOptions"]["SessionTimeout"], int)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])