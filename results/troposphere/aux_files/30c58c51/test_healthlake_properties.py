#!/usr/bin/env python3
"""Property-based tests for troposphere.healthlake module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import pytest
import json
from troposphere import healthlake
from troposphere.validators import boolean, integer


# Test 1: Boolean validator consistency
@given(st.one_of(
    st.just(True), st.just(False),
    st.just(1), st.just(0),
    st.just("1"), st.just("0"),
    st.just("true"), st.just("false"),
    st.just("True"), st.just("False"),
))
def test_boolean_validator_consistency(value):
    """Test that boolean validator consistently converts accepted values."""
    result = boolean(value)
    assert isinstance(result, bool)
    
    # Check that it's idempotent - applying boolean twice should give same result
    result2 = boolean(result)
    assert result == result2
    
    # Check expected conversions
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


# Test 2: Boolean validator rejects invalid inputs
@given(st.one_of(
    st.integers(min_value=2),
    st.integers(max_value=-1),
    st.text(min_size=1).filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
))
def test_boolean_validator_invalid(value):
    """Test that boolean validator rejects invalid inputs."""
    with pytest.raises(ValueError):
        boolean(value)


# Test 3: Integer validator properties
@given(st.one_of(
    st.integers(),
    st.text(min_size=1).map(lambda x: str(int.from_bytes(x.encode()[:8], 'little', signed=True))),
))
def test_integer_validator_valid(value):
    """Test that integer validator accepts valid integer-like values."""
    result = integer(value)
    # Should be convertible to int
    int(result)


# Test 4: Integer validator with non-integer strings
@given(st.text(min_size=1).filter(lambda x: not x.strip().lstrip('-').isdigit() if x.strip() else True))
def test_integer_validator_invalid_strings(value):
    """Test that integer validator rejects non-integer strings."""
    assume(value.strip())  # Skip empty strings
    try:
        int(value)
        # If Python's int() accepts it, integer validator should too
        integer(value)
    except (ValueError, TypeError):
        # If Python's int() rejects it, integer validator should too
        with pytest.raises(ValueError):
            integer(value)


# Test 5: CreatedAt class validation
@given(
    nanos=st.one_of(st.integers(), st.text()),
    seconds=st.text()
)
def test_created_at_property_types(nanos, seconds):
    """Test CreatedAt class property type validation."""
    try:
        # Try to create a CreatedAt instance
        created_at = healthlake.CreatedAt(Nanos=nanos, Seconds=seconds)
        
        # If successful, nanos should have passed integer validation
        try:
            int(nanos)
            nanos_valid = True
        except (ValueError, TypeError):
            nanos_valid = False
            
        assert nanos_valid, f"CreatedAt accepted invalid Nanos value: {nanos}"
        
        # Check we can convert to dict
        d = created_at.to_dict()
        assert isinstance(d, dict)
        
    except (ValueError, TypeError) as e:
        # Should only fail if nanos is not integer-like
        try:
            int(nanos)
            # If nanos was valid, this is unexpected
            raise AssertionError(f"CreatedAt rejected valid Nanos value: {nanos}")
        except (ValueError, TypeError):
            # Expected - nanos was invalid
            pass


# Test 6: Required properties enforcement
def test_identity_provider_configuration_required():
    """Test that required properties are enforced."""
    # AuthorizationStrategy is required
    with pytest.raises(ValueError) as exc_info:
        config = healthlake.IdentityProviderConfiguration()
        config.to_dict()  # Validation happens here
    assert "AuthorizationStrategy" in str(exc_info.value)


# Test 7: PreloadDataConfig required property
def test_preload_data_config_required():
    """Test PreloadDataConfig requires PreloadDataType."""
    with pytest.raises(ValueError) as exc_info:
        config = healthlake.PreloadDataConfig()
        config.to_dict()  # Validation happens here
    assert "PreloadDataType" in str(exc_info.value)


# Test 8: KmsEncryptionConfig required property
def test_kms_encryption_config_required():
    """Test KmsEncryptionConfig requires CmkType."""
    with pytest.raises(ValueError) as exc_info:
        config = healthlake.KmsEncryptionConfig()
        config.to_dict()  # Validation happens here
    assert "CmkType" in str(exc_info.value)


# Test 9: FHIRDatastore required property
def test_fhir_datastore_required():
    """Test FHIRDatastore requires DatastoreTypeVersion."""
    with pytest.raises(ValueError) as exc_info:
        datastore = healthlake.FHIRDatastore("TestDatastore")
        datastore.to_dict()  # Validation happens here
    assert "DatastoreTypeVersion" in str(exc_info.value)


# Test 10: Round-trip property - to_dict and from_dict
@given(
    name=st.text(alphabet=st.characters(whitelist_categories=['L', 'N']), min_size=1, max_size=50),
    version=st.text(min_size=1, max_size=20),
)
def test_fhir_datastore_round_trip(name, version):
    """Test that FHIRDatastore can round-trip through dict representation."""
    # Create a datastore with required properties
    datastore1 = healthlake.FHIRDatastore(
        name,
        DatastoreTypeVersion=version,
        DatastoreName=f"Store_{name}"
    )
    
    # Convert to dict
    dict1 = datastore1.to_dict()
    
    # Create new instance from dict
    datastore2 = healthlake.FHIRDatastore.from_dict(
        name,
        dict1.get("Properties", {})
    )
    
    # Convert back to dict
    dict2 = datastore2.to_dict()
    
    # Should be equal
    assert dict1 == dict2


# Test 11: Property type enforcement with invalid types
@given(
    invalid_value=st.one_of(
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.floats(),
    )
)
def test_created_at_type_enforcement(invalid_value):
    """Test that CreatedAt enforces correct types for properties."""
    # Nanos should be integer-like
    try:
        created_at = healthlake.CreatedAt(Nanos=invalid_value, Seconds="100")
        created_at.to_dict()
        # If it succeeded, the value should be integer-like
        int(invalid_value)
    except (ValueError, TypeError):
        # Expected - should reject non-integer values
        pass


# Test 12: Test boolean property in actual AWS class
@given(
    enabled=st.one_of(
        st.just(True), st.just(False),
        st.just(1), st.just(0),
        st.just("true"), st.just("false"),
        st.just("True"), st.just("False"),
    )
)
def test_identity_provider_boolean_property(enabled):
    """Test that boolean properties work correctly in IdentityProviderConfiguration."""
    config = healthlake.IdentityProviderConfiguration(
        AuthorizationStrategy="SMART_ON_FHIR_V1",
        FineGrainedAuthorizationEnabled=enabled
    )
    
    d = config.to_dict()
    
    # The boolean value should be normalized
    result = d["FineGrainedAuthorizationEnabled"]
    assert isinstance(result, bool)
    
    if enabled in [True, 1, "true", "True"]:
        assert result is True
    else:
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])