"""Additional edge case testing for troposphere.wafv2 validation functions"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from troposphere.validators.wafv2 import (
    validate_transformation_type,
    validate_comparison_operator,
    validate_ipaddress_version,
    validate_positional_constraint,
    wafv2_custom_body_response_content,
    wafv2_custom_body_response_content_type,
    validate_custom_response_bodies,
)
from troposphere.wafv2 import CustomResponseBody


# Test unicode and special characters
@given(st.text(alphabet=st.characters(blacklist_categories=('Cs',))))
@settings(max_examples=500)
def test_validators_handle_unicode_correctly(text):
    """Test that validators handle unicode text correctly"""
    
    # Test transformation type validator
    VALID_TRANSFORMATION_TYPES = {
        "BASE64_DECODE", "BASE64_DECODE_EXT", "CMD_LINE", "COMPRESS_WHITE_SPACE",
        "CSS_DECODE", "ESCAPE_SEQ_DECODE", "HEX_DECODE", "HTML_ENTITY_DECODE",
        "JS_DECODE", "LOWERCASE", "MD5", "NONE", "NORMALIZE_PATH",
        "NORMALIZE_PATH_WIN", "REMOVE_NULLS", "REPLACE_COMMENTS", "REPLACE_NULLS",
        "SQL_HEX_DECODE", "URL_DECODE", "URL_DECODE_UNI", "UTF8_TO_UNICODE"
    }
    
    if text not in VALID_TRANSFORMATION_TYPES:
        with pytest.raises(ValueError):
            validate_transformation_type(text)


# Test null bytes and control characters
@given(st.text(alphabet=st.sampled_from(["\x00", "\x01", "\x02", "\n", "\r", "\t"])))
def test_validators_handle_control_characters(text):
    """Test validators with control characters"""
    
    # These should all be rejected as invalid
    with pytest.raises(ValueError):
        validate_comparison_operator(text)
    
    with pytest.raises(ValueError):
        validate_ipaddress_version(text)
    
    with pytest.raises(ValueError):
        validate_positional_constraint(text)


# Test empty strings for validators
def test_validators_reject_empty_strings():
    """Test that validators properly reject empty strings"""
    
    with pytest.raises(ValueError):
        validate_transformation_type("")
    
    with pytest.raises(ValueError):
        validate_comparison_operator("")
    
    with pytest.raises(ValueError):
        validate_ipaddress_version("")
    
    with pytest.raises(ValueError):
        validate_positional_constraint("")
    
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content_type("")


# Test with mixed case variations of valid values
@given(st.sampled_from([
    "ipv4", "Ipv4", "iPv4", "IPV4", "ipV4",
    "ipv6", "Ipv6", "iPv6", "IPV6", "ipV6"
]))
def test_ipaddress_version_case_sensitivity(version):
    """Test that IP version validator is strictly case-sensitive"""
    
    if version in {"IPV4", "IPV6"}:
        result = validate_ipaddress_version(version)
        assert result == version
    else:
        with pytest.raises(ValueError) as exc_info:
            validate_ipaddress_version(version)
        assert "IPSet IPAddressVersion must be one of" in str(exc_info.value)


# Test content with exactly boundary values
@given(st.sampled_from([0, 1, 10239, 10240, 10241]))
def test_content_exact_boundaries(length):
    """Test exact boundary conditions for content length"""
    
    content = "x" * length
    
    if length == 0:
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content must not be empty" in str(exc_info.value)
    elif length > 10240:
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content maximum length must not exceed 10240" in str(exc_info.value)
    else:
        result = wafv2_custom_body_response_content(content)
        assert result == content
        assert len(result) == length


# Test with None values
def test_validators_handle_none():
    """Test that validators properly handle None inputs"""
    
    # Most should raise TypeError or AttributeError
    with pytest.raises((TypeError, AttributeError)):
        validate_transformation_type(None)
    
    with pytest.raises((TypeError, AttributeError)):
        validate_comparison_operator(None)
    
    with pytest.raises((TypeError, AttributeError)):
        validate_ipaddress_version(None)
    
    with pytest.raises((TypeError, AttributeError)):
        validate_positional_constraint(None)
    
    # This one checks for empty content
    with pytest.raises((TypeError, AttributeError, ValueError)):
        wafv2_custom_body_response_content(None)
    
    with pytest.raises((TypeError, AttributeError)):
        wafv2_custom_body_response_content_type(None)


# Test whitespace-only strings
@given(st.text(alphabet=" \t\n\r", min_size=1, max_size=10))
def test_validators_with_whitespace_only(whitespace):
    """Test validators with whitespace-only strings"""
    
    # Should all be rejected as invalid values
    with pytest.raises(ValueError):
        validate_transformation_type(whitespace)
    
    with pytest.raises(ValueError):
        validate_comparison_operator(whitespace)
    
    with pytest.raises(ValueError):
        validate_ipaddress_version(whitespace)
    
    with pytest.raises(ValueError):
        validate_positional_constraint(whitespace)
    
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content_type(whitespace)
    
    # Content validator should accept whitespace (it's valid content)
    if len(whitespace) <= 10240:
        result = wafv2_custom_body_response_content(whitespace)
        assert result == whitespace


# Test valid values with leading/trailing whitespace
@given(st.sampled_from([" IPV4", "IPV4 ", " IPV4 ", "\tIPV4", "IPV4\n"]))
def test_validators_reject_whitespace_padded_valid_values(value):
    """Test that validators don't strip whitespace from valid values"""
    
    # Should reject because of whitespace
    with pytest.raises(ValueError):
        validate_ipaddress_version(value)


# Test custom_response_bodies with non-dict types
@given(st.one_of(
    st.lists(st.text()),
    st.text(),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.none()
))
def test_custom_response_bodies_requires_dict(value):
    """Test that validate_custom_response_bodies only accepts dicts"""
    
    if not isinstance(value, dict):
        with pytest.raises(ValueError) as exc_info:
            validate_custom_response_bodies(value)
        assert "CustomResponseBodies must be dict" in str(exc_info.value)


# Test very long strings for content validation
@given(st.integers(min_value=10241, max_value=100000))
@settings(max_examples=50)
def test_content_rejects_very_long_strings(length):
    """Test that content validator properly rejects very long strings"""
    
    # Use a generator to avoid memory issues with huge strings
    content = "a" * length
    
    with pytest.raises(ValueError) as exc_info:
        wafv2_custom_body_response_content(content)
    assert "Content maximum length must not exceed 10240" in str(exc_info.value)


# Test content with multibyte unicode characters
@given(st.text(alphabet="🔥💀🎉🦄🚀", min_size=0, max_size=5000))
def test_content_with_emoji_counts_characters_not_bytes(content):
    """Test that content length is counted in characters, not bytes"""
    
    char_count = len(content)
    
    if char_count == 0:
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content must not be empty" in str(exc_info.value)
    elif char_count > 10240:
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content maximum length must not exceed 10240" in str(exc_info.value)
    else:
        result = wafv2_custom_body_response_content(content)
        assert result == content
        assert len(result) == char_count