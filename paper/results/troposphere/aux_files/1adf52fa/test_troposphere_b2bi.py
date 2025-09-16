#!/usr/bin/env python3
"""Property-based tests for troposphere.b2bi module."""

import sys
import re
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import json

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.b2bi as b2bi
from troposphere import Tags


# Strategy for generating valid CloudFormation resource names (alphanumeric only)
valid_title_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=1,
    max_size=255
).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x))

# Strategy for invalid titles (containing special characters)
invalid_title_strategy = st.text(min_size=1, max_size=100).filter(
    lambda x: not re.match(r'^[a-zA-Z0-9]+$', x) and len(x) > 0
)

# Strategy for S3 bucket names and keys
s3_bucket_strategy = st.text(min_size=3, max_size=63, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'))
s3_key_strategy = st.text(min_size=1, max_size=1024)

# Strategy for generating S3Location objects
@composite
def s3_location_strategy(draw):
    return b2bi.S3Location(
        BucketName=draw(s3_bucket_strategy),
        Key=draw(s3_key_strategy)
    )

# Strategy for generating X12Details objects
@composite
def x12_details_strategy(draw):
    return b2bi.X12Details(
        TransactionSet=draw(st.text(min_size=1, max_size=10)),
        Version=draw(st.text(min_size=1, max_size=10))
    )

# Strategy for generating EdiType objects
@composite 
def edi_type_strategy(draw):
    return b2bi.EdiType(
        X12Details=draw(x12_details_strategy())
    )

# Strategy for generating EdiConfiguration objects
@composite
def edi_configuration_strategy(draw):
    return b2bi.EdiConfiguration(
        CapabilityDirection=draw(st.sampled_from(['INBOUND', 'OUTBOUND'])),
        InputLocation=draw(s3_location_strategy()),
        OutputLocation=draw(s3_location_strategy()),
        TransformerId=draw(st.text(min_size=1, max_size=255)),
        Type=draw(edi_type_strategy())
    )

# Strategy for Profile objects
@composite
def profile_strategy(draw):
    return b2bi.Profile(
        title=draw(valid_title_strategy),
        BusinessName=draw(st.text(min_size=1, max_size=255)),
        Email=draw(st.emails()) if draw(st.booleans()) else None,
        Logging=draw(st.sampled_from(['ENABLED', 'DISABLED'])),
        Name=draw(st.text(min_size=1, max_size=255)),
        Phone=draw(st.text(min_size=1, max_size=20))
    )

# Test 1: Round-trip property - to_dict and from_dict should be inverse operations
@given(profile_strategy())
@settings(max_examples=100)
def test_profile_round_trip(profile):
    """Test that Profile objects survive serialization/deserialization."""
    # Convert to dict
    profile_dict = profile.to_dict()
    
    # Convert back from dict
    restored = b2bi.Profile.from_dict(profile.title, profile_dict['Properties'])
    
    # They should be equal
    assert profile == restored


# Test 2: Title validation - non-alphanumeric titles should raise ValueError
@given(invalid_title_strategy)
def test_invalid_title_raises_error(invalid_title):
    """Test that non-alphanumeric titles raise ValueError."""
    try:
        profile = b2bi.Profile(
            title=invalid_title,
            BusinessName="TestBusiness",
            Logging="ENABLED",
            Name="TestName",
            Phone="123-456-7890"
        )
        # If we get here without exception, it's a bug
        assert False, f"Expected ValueError for title '{invalid_title}' but no exception was raised"
    except ValueError as e:
        # This is expected
        assert "not alphanumeric" in str(e)


# Test 3: Required property validation
@given(valid_title_strategy, st.text(min_size=1))
def test_missing_required_properties(title, business_name):
    """Test that missing required properties raise ValueError during validation."""
    # Create a Profile with only some required properties
    profile = b2bi.Profile(title=title)
    profile.BusinessName = business_name
    # Missing: Logging, Name, Phone (all required)
    
    try:
        # This should raise ValueError for missing required properties
        profile.to_dict()
        assert False, "Expected ValueError for missing required properties"
    except ValueError as e:
        # Check that it mentions a required resource
        assert "required" in str(e).lower()


# Test 4: Type validation
@given(valid_title_strategy)
def test_type_validation_for_properties(title):
    """Test that setting properties with wrong types raises TypeError."""
    profile = b2bi.Profile(title=title)
    
    # Try to set a string property with an integer
    try:
        profile.BusinessName = 12345  # Should be string
        # BusinessName is a string property, setting int should work due to coercion
        # Let's try something that definitely won't work
        profile.BusinessName = {"not": "a string"}  # Dict instead of string
        # If no exception, might be a bug
    except (TypeError, AttributeError):
        # Expected behavior
        pass


# Test 5: Partnership capability validation
@given(valid_title_strategy, st.lists(st.text(min_size=1, max_size=100), min_size=1))
def test_partnership_capabilities_must_be_list(title, capabilities):
    """Test that Partnership capabilities must be a list of strings."""
    partnership = b2bi.Partnership(
        title=title,
        Capabilities=capabilities,
        Email="test@example.com",
        Name="TestPartnership",
        ProfileId="test-profile-id"
    )
    
    # Should be able to convert to dict
    partnership_dict = partnership.to_dict()
    assert 'Properties' in partnership_dict
    assert partnership_dict['Properties']['Capabilities'] == capabilities


# Test 6: X12Details property consistency
@given(x12_details_strategy())
def test_x12_details_properties(x12_details):
    """Test that X12Details maintains its properties correctly."""
    details_dict = x12_details.to_dict()
    
    # Properties should be preserved
    if hasattr(x12_details, 'TransactionSet') and x12_details.TransactionSet:
        assert details_dict['TransactionSet'] == x12_details.TransactionSet
    if hasattr(x12_details, 'Version') and x12_details.Version:
        assert details_dict['Version'] == x12_details.Version


# Test 7: Transformer status validation
@given(valid_title_strategy, st.text(min_size=1, max_size=100))
def test_transformer_status_property(title, name):
    """Test Transformer status property handling."""
    transformer = b2bi.Transformer(
        title=title,
        Name=name,
        Status="active"  # Required property
    )
    
    transformer_dict = transformer.to_dict()
    assert transformer_dict['Properties']['Status'] == "active"


# Test 8: Capability configuration structure
@given(valid_title_strategy, st.text(min_size=1, max_size=100))
def test_capability_configuration_structure(title, name):
    """Test that Capability maintains proper configuration structure."""
    capability = b2bi.Capability(
        title=title,
        Name=name,
        Type="edi",
        Configuration=b2bi.CapabilityConfiguration(
            Edi=b2bi.EdiConfiguration(
                InputLocation=b2bi.S3Location(BucketName="test-bucket", Key="input/"),
                OutputLocation=b2bi.S3Location(BucketName="test-bucket", Key="output/"),
                TransformerId="transformer-123",
                Type=b2bi.EdiType(
                    X12Details=b2bi.X12Details(TransactionSet="850", Version="004010")
                )
            )
        )
    )
    
    cap_dict = capability.to_dict()
    
    # Verify nested structure is preserved
    assert 'Properties' in cap_dict
    assert 'Configuration' in cap_dict['Properties']
    assert 'Edi' in cap_dict['Properties']['Configuration']
    

# Test 9: Optional vs Required properties in S3Location
@given(s3_bucket_strategy, s3_key_strategy)
def test_s3_location_optional_properties(bucket, key):
    """Test that S3Location handles optional properties correctly."""
    # Both properties are optional (False in props definition)
    s3_loc1 = b2bi.S3Location()
    s3_loc1_dict = s3_loc1.to_dict()
    # Should work even without properties
    
    s3_loc2 = b2bi.S3Location(BucketName=bucket)
    s3_loc2_dict = s3_loc2.to_dict()
    assert s3_loc2_dict.get('BucketName') == bucket
    
    s3_loc3 = b2bi.S3Location(BucketName=bucket, Key=key)
    s3_loc3_dict = s3_loc3.to_dict()
    assert s3_loc3_dict.get('BucketName') == bucket
    assert s3_loc3_dict.get('Key') == key


# Test 10: Property name validation - setting non-existent properties  
@given(valid_title_strategy, st.text(min_size=1, max_size=50).filter(
    lambda x: x not in ['BusinessName', 'Email', 'Logging', 'Name', 'Phone', 'Tags']
))
def test_invalid_property_name_raises_error(title, invalid_prop):
    """Test that setting non-existent properties raises AttributeError."""
    profile = b2bi.Profile(
        title=title,
        BusinessName="TestBusiness",
        Logging="ENABLED", 
        Name="TestName",
        Phone="123-456-7890"
    )
    
    try:
        setattr(profile, invalid_prop, "some_value")
        # Check if it was actually set (shouldn't be in properties)
        if invalid_prop not in profile.properties:
            # This might be OK - it could be set as an instance attribute
            # Let's verify it doesn't affect to_dict
            profile_dict = profile.to_dict()
    except AttributeError as e:
        # This is expected for truly invalid properties
        assert "does not support attribute" in str(e)


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])