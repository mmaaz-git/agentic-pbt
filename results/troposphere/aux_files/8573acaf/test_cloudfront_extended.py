"""Extended property-based tests for troposphere.cloudfront module with more examples"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest

# Import the modules we're testing
from troposphere import cloudfront, validators
from troposphere.validators import cloudfront as cf_validators
from troposphere import Tag, Tags


# Test with edge case: Test integer boundary for network_port
@given(st.sampled_from([-2, -1, 0, 65535, 65536]))
@settings(max_examples=1000)
def test_network_port_boundaries(port):
    """Test exact boundaries of network_port validator"""
    if -1 <= port <= 65535:
        result = validators.network_port(port)
        assert result == port
    else:
        with pytest.raises(ValueError):
            validators.network_port(port)


# Test edge case: Empty lists for validators that expect lists
def test_empty_list_for_methods():
    """Test empty list for access control methods"""
    # Empty list should be accepted since all elements vacuously satisfy the constraint
    result = cf_validators.cloudfront_access_control_allow_methods([])
    assert result == []


# Test with None values
def test_none_values_in_validators():
    """Test how validators handle None values"""
    
    # Integer validator with None
    with pytest.raises(ValueError, match="is not a valid integer"):
        validators.integer(None)
    
    # Double validator with None  
    with pytest.raises(ValueError, match="is not a valid double"):
        validators.double(None)
    
    # Boolean validator with None
    with pytest.raises(ValueError):
        validators.boolean(None)


# Test string representations of numbers in boolean
@given(st.text())
def test_boolean_with_arbitrary_strings(s):
    """Test boolean validator with arbitrary strings"""
    if s in ["1", "true", "True", "0", "false", "False"]:
        # These should work
        result = validators.boolean(s)
        assert isinstance(result, bool)
    else:
        # Everything else should fail
        with pytest.raises(ValueError):
            validators.boolean(s)


# Test with very large integers for network port
@given(st.integers(min_value=65536, max_value=2**31))
def test_network_port_large_values(port):
    """Test network_port with very large values"""
    with pytest.raises(ValueError, match="network port .* must been between 0 and 65535"):
        validators.network_port(port)


@given(st.integers(max_value=-2))
def test_network_port_negative_values(port):
    """Test network_port with negative values below -1"""
    with pytest.raises(ValueError, match="network port .* must been between 0 and 65535"):
        validators.network_port(port)


# Test boolean with numeric strings that aren't "0" or "1"
@given(st.text(alphabet="0123456789", min_size=1).filter(lambda x: x not in ["0", "1"]))
def test_boolean_with_numeric_strings(s):
    """Test boolean validator with numeric strings other than 0 and 1"""
    with pytest.raises(ValueError):
        validators.boolean(s)


# Test case sensitivity in enum validators
def test_case_sensitivity_in_enums():
    """Test that enum validators are case-sensitive"""
    
    # These should fail - wrong case
    with pytest.raises(ValueError):
        cf_validators.cloudfront_cache_cookie_behavior("None")  # should be "none"
    
    with pytest.raises(ValueError):
        cf_validators.cloudfront_cache_cookie_behavior("NONE")
    
    with pytest.raises(ValueError):
        cf_validators.cloudfront_viewer_protocol_policy("Allow-All")  # should be "allow-all"
    
    with pytest.raises(ValueError):
        cf_validators.cloudfront_restriction_type("Blacklist")  # should be "blacklist"


# Test mixed-type lists for method validator
def test_mixed_type_list_for_methods():
    """Test that method validator rejects non-list inputs"""
    
    # Should reject non-list inputs
    with pytest.raises(TypeError, match="AccessControlAllowMethods is not a list"):
        cf_validators.cloudfront_access_control_allow_methods("GET")
    
    with pytest.raises(TypeError, match="AccessControlAllowMethods is not a list"):
        cf_validators.cloudfront_access_control_allow_methods({"GET": True})


# Test partial matches in enum validators
@given(st.text(min_size=1))
def test_no_partial_matches_in_enums(value):
    """Test that enum validators don't accept partial matches"""
    
    # Test viewer protocol policy - no partial matches
    valid_policies = ["allow-all", "redirect-to-https", "https-only"]
    if value not in valid_policies:
        with pytest.raises(ValueError):
            cf_validators.cloudfront_viewer_protocol_policy(value)


# Test validate_tags_items_array with wrong structure
def test_tags_validation_wrong_structure():
    """Test validate_tags_items_array with various wrong structures"""
    
    # Multiple keys in dict
    with pytest.raises(ValueError, match="Tags must be a dictionary with a single key 'Items'"):
        cf_validators.validate_tags_items_array({"Items": [], "Other": []})
    
    # Wrong key name
    with pytest.raises(ValueError, match="Tags must be a dictionary with a single key 'Items'"):
        cf_validators.validate_tags_items_array({"items": []})
    
    # Not a dict
    with pytest.raises(ValueError, match="Tags must be a dictionary with a single key 'Items'"):
        cf_validators.validate_tags_items_array([])
    
    # Items contains non-Tag objects
    with pytest.raises(ValueError, match="Items array in Tags must contain Tag objects"):
        cf_validators.validate_tags_items_array({"Items": ["not a tag"]})


# Test integer validator with float strings
@given(st.floats(allow_nan=False, allow_infinity=False).map(str))
def test_integer_with_float_strings(s):
    """Test integer validator with string representations of floats"""
    try:
        # If it can be converted to int without error, it should pass
        int(float(s))
        if '.' not in s and 'e' not in s.lower():
            # Looks like an integer string
            result = validators.integer(s)
            assert result == s
    except (ValueError, OverflowError):
        # Should fail validation
        with pytest.raises(ValueError, match="is not a valid integer"):
            validators.integer(s)


# Test Properties with invalid types
def test_cache_policy_ttl_validation():
    """Test that TTL values in CachePolicyConfig are validated as doubles"""
    config = cloudfront.CachePolicyConfig(
        DefaultTTL=3600.5,  # Double value
        MaxTTL=86400,       # Integer that should be accepted as double
        MinTTL=0,           # Zero
        Name="TestPolicy",
        ParametersInCacheKeyAndForwardedToOrigin=cloudfront.ParametersInCacheKeyAndForwardedToOrigin(
            CookiesConfig=cloudfront.CacheCookiesConfig(CookieBehavior="none"),
            EnableAcceptEncodingGzip=True,
            HeadersConfig=cloudfront.CacheHeadersConfig(HeaderBehavior="none"),
            QueryStringsConfig=cloudfront.CacheQueryStringsConfig(QueryStringBehavior="none")
        )
    )
    
    # Should have accepted the values
    assert config.properties["DefaultTTL"] == 3600.5
    assert config.properties["MaxTTL"] == 86400
    assert config.properties["MinTTL"] == 0


# Test for integer overflow in validators
@given(st.integers(min_value=2**63, max_value=2**100))
def test_integer_overflow(big_int):
    """Test integer validator with very large integers"""
    # Python can handle arbitrarily large integers, so this should work
    result = validators.integer(big_int)
    assert result == big_int


# Test StatusCodes with invalid integer list
def test_status_codes_validation():
    """Test StatusCodes with valid structure"""
    # Valid case
    status = cloudfront.StatusCodes(
        Items=[403, 404, 500, 502],
        Quantity=4
    )
    assert status.properties["Items"] == [403, 404, 500, 502]
    assert status.properties["Quantity"] == 4


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])