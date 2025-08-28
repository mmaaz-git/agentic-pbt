"""Property-based tests for troposphere.cloudfront module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, assume, strategies as st, settings
import pytest

# Import the modules we're testing
from troposphere import cloudfront, validators
from troposphere.validators import cloudfront as cf_validators
from troposphere import Tag, Tags


# Test 1: network_port validator - port range property
@given(st.integers())
def test_network_port_validator_range(port):
    """network_port should accept -1 to 65535 and reject values outside"""
    if -1 <= port <= 65535:
        # Should not raise
        result = validators.network_port(port)
        assert result == port
    else:
        # Should raise ValueError
        with pytest.raises(ValueError, match="network port .* must been between 0 and 65535"):
            validators.network_port(port)


# Test 2: boolean validator - mapping property
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(),
    st.integers(),
    st.floats(),
    st.none()
))
def test_boolean_validator_mapping(value):
    """boolean validator should correctly map known values and reject unknown"""
    if value in [True, 1, "1", "true", "True"]:
        assert validators.boolean(value) is True
    elif value in [False, 0, "0", "false", "False"]:
        assert validators.boolean(value) is False
    else:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test 3: CloudFront enum validators - allowed values only
@given(st.text())
def test_cloudfront_cache_cookie_behavior_enum(value):
    """cloudfront_cache_cookie_behavior should only accept specific values"""
    valid_values = ["none", "whitelist", "allExcept", "all"]
    if value in valid_values:
        assert cf_validators.cloudfront_cache_cookie_behavior(value) == value
    else:
        with pytest.raises(ValueError, match="CookieBehavior must be one of"):
            cf_validators.cloudfront_cache_cookie_behavior(value)


@given(st.text())
def test_cloudfront_viewer_protocol_policy_enum(value):
    """cloudfront_viewer_protocol_policy should only accept specific values"""
    valid_values = ["allow-all", "redirect-to-https", "https-only"]
    if value in valid_values:
        assert cf_validators.cloudfront_viewer_protocol_policy(value) == value
    else:
        with pytest.raises(ValueError, match="ViewerProtocolPolicy must be one of"):
            cf_validators.cloudfront_viewer_protocol_policy(value)


@given(st.lists(st.text()))
def test_cloudfront_access_control_allow_methods_list(methods):
    """cloudfront_access_control_allow_methods should validate list of methods"""
    valid_values = ["GET", "DELETE", "HEAD", "OPTIONS", "PATCH", "POST", "PUT", "ALL"]
    
    if all(m in valid_values for m in methods):
        assert cf_validators.cloudfront_access_control_allow_methods(methods) == methods
    elif any(m not in valid_values for m in methods):
        with pytest.raises(ValueError, match="AccessControlAllowMethods must be one of"):
            cf_validators.cloudfront_access_control_allow_methods(methods)


# Test 4: validate_tags_items_array structure validation
@given(st.one_of(
    st.dictionaries(st.text(), st.text()),
    st.lists(st.text()),
    st.none(),
    st.dictionaries(
        st.sampled_from(["Items"]), 
        st.lists(st.one_of(
            st.builds(Tag, st.text(), st.text()),
            st.text(),
            st.integers()
        ))
    )
))
def test_validate_tags_items_array_structure(value):
    """validate_tags_items_array should validate dict with Items key containing Tags"""
    # Valid case: dict with "Items" key containing list of Tag objects
    if isinstance(value, dict) and len(value) == 1 and "Items" in value:
        if all(isinstance(item, Tag) for item in value["Items"]):
            result = cf_validators.validate_tags_items_array(value)
            assert result == value
        else:
            with pytest.raises(ValueError, match="Items array in Tags must contain Tag objects"):
                cf_validators.validate_tags_items_array(value)
    else:
        with pytest.raises(ValueError, match="Tags must be a dictionary with a single key 'Items'"):
            cf_validators.validate_tags_items_array(value)


# Test 5: integer validator
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator(value):
    """integer validator should accept valid integers and reject non-integers"""
    try:
        int(value)
        # Should not raise
        result = validators.integer(value)
        assert result == value
    except (ValueError, TypeError):
        # Should raise ValueError with specific message
        with pytest.raises(ValueError, match="is not a valid integer"):
            validators.integer(value)


# Test 6: double validator
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(),
    st.none(),
    st.lists(st.floats())
))
def test_double_validator(value):
    """double validator should accept valid floats and reject non-floats"""
    try:
        float(value)
        # Should not raise
        result = validators.double(value)
        assert result == value
    except (ValueError, TypeError):
        # Should raise ValueError with specific message
        with pytest.raises(ValueError, match="is not a valid double"):
            validators.double(value)


# Test 7: priceclass_type validator
@given(st.text())
def test_priceclass_type_enum(value):
    """priceclass_type should only accept specific values"""
    valid_values = ["PriceClass_100", "PriceClass_200", "PriceClass_All"]
    if value in valid_values:
        assert cf_validators.priceclass_type(value) == value
    else:
        with pytest.raises(ValueError, match="PriceClass must be one of"):
            cf_validators.priceclass_type(value)


# Test 8: cloudfront_restriction_type validator
@given(st.text())
def test_cloudfront_restriction_type_enum(value):
    """cloudfront_restriction_type should only accept specific values"""
    valid_values = ["none", "blacklist", "whitelist"]
    if value in valid_values:
        assert cf_validators.cloudfront_restriction_type(value) == value
    else:
        with pytest.raises(ValueError, match="RestrictionType must be one of"):
            cf_validators.cloudfront_restriction_type(value)


# Test 9: Property assignment consistency - testing that validators are applied
@given(st.integers())
@settings(max_examples=200)
def test_custom_origin_config_port_validation(port):
    """CustomOriginConfig should validate HTTP/HTTPS ports using network_port validator"""
    config_dict = {
        "OriginProtocolPolicy": "https-only"
    }
    
    if -1 <= port <= 65535:
        # Should not raise
        config_dict["HTTPPort"] = port
        config = cloudfront.CustomOriginConfig(**config_dict)
        assert config.properties.get("HTTPPort") == port
    else:
        # Should raise ValueError from network_port validator
        config_dict["HTTPPort"] = port
        with pytest.raises(ValueError, match="network port .* must been between 0 and 65535"):
            cloudfront.CustomOriginConfig(**config_dict)


# Test 10: Round-trip property - setting and getting properties
@given(
    st.text(min_size=1),
    st.sampled_from(["allow-all", "redirect-to-https", "https-only"])
)
def test_default_cache_behavior_properties_roundtrip(target_id, viewer_policy):
    """Properties set on DefaultCacheBehavior should be retrievable"""
    behavior = cloudfront.DefaultCacheBehavior(
        TargetOriginId=target_id,
        ViewerProtocolPolicy=viewer_policy
    )
    
    assert behavior.TargetOriginId == target_id
    assert behavior.ViewerProtocolPolicy == viewer_policy


# Test 11: Test cloudfront_event_type validator
@given(st.text())
def test_cloudfront_event_type_enum(value):
    """cloudfront_event_type should only accept specific event types"""
    valid_values = [
        "viewer-request",
        "viewer-response", 
        "origin-request",
        "origin-response"
    ]
    if value in valid_values:
        assert cf_validators.cloudfront_event_type(value) == value
    else:
        with pytest.raises(ValueError, match="EventType must be one of"):
            cf_validators.cloudfront_event_type(value)


# Test 12: Metamorphic property - multiple ways to set boolean values
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_true_equivalence(value):
    """All True-like values should map to True"""
    assert validators.boolean(value) is True
    
    # Test in actual usage
    grpc = cloudfront.GrpcConfig(Enabled=value)
    # The validator should normalize all these to True
    assert grpc.properties["Enabled"] is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_false_equivalence(value):
    """All False-like values should map to False"""
    assert validators.boolean(value) is False
    
    # Test in actual usage
    grpc = cloudfront.GrpcConfig(Enabled=value)
    # The validator should normalize all these to False
    assert grpc.properties["Enabled"] is False


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])