"""Comprehensive property-based tests to find bugs in troposphere.wafv2"""

import pytest
from hypothesis import given, strategies as st, settings, assume, example
from troposphere.validators.wafv2 import (
    validate_transformation_type,
    validate_comparison_operator,
    validate_ipaddress_version,
    validate_positional_constraint,
    wafv2_custom_body_response_content,
    wafv2_custom_body_response_content_type,
    validate_statements,
    validate_statement,
    validate_custom_response_bodies,
)
from troposphere.wafv2 import Statement, CustomResponseBody
from troposphere import AWSHelperFn
import string


# Test for confusion between string "NONE" and Python None
def test_transformation_type_none_confusion():
    """Test that string 'NONE' is accepted but Python None is not"""
    
    # String "NONE" should be accepted (it's a valid transformation type)
    result = validate_transformation_type("NONE")
    assert result == "NONE"
    
    # Python None should be rejected
    with pytest.raises(ValueError):
        validate_transformation_type(None)


# Test for potential integer/string confusion
@given(st.integers())
def test_validators_reject_integers(value):
    """Test that validators properly reject integer inputs"""
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_transformation_type(value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_comparison_operator(value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_ipaddress_version(value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_positional_constraint(value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        wafv2_custom_body_response_content_type(value)


# Test for SQL injection-like patterns in validators
@given(st.sampled_from([
    "'; DROP TABLE--",
    "OR 1=1",
    "IPV4' OR 'IPV6",
    "IPV4/*comment*/",
    "IPV4\x00IPV6",
    "../../../etc/passwd",
    "IPV4\nIPV6",
]))
def test_validators_reject_injection_attempts(value):
    """Test that validators properly reject injection-like strings"""
    
    # None of these should be valid values
    with pytest.raises(ValueError):
        validate_ipaddress_version(value)
    
    with pytest.raises(ValueError):
        validate_transformation_type(value)


# Test statement validation with edge cases
def test_validate_statement_edge_cases():
    """Test validate_statement with various edge cases"""
    
    # Valid Statement should pass
    stmt = Statement()
    result = validate_statement(stmt)
    assert result == stmt
    
    # AWSHelperFn should pass
    class MockHelperFn(AWSHelperFn):
        def __init__(self):
            pass
    
    helper = MockHelperFn()
    result = validate_statement(helper)
    assert result == helper
    
    # Other types should fail
    with pytest.raises(TypeError):
        validate_statement("not a statement")
    
    with pytest.raises(TypeError):
        validate_statement(123)
    
    with pytest.raises(TypeError):
        validate_statement(None)
    
    with pytest.raises(TypeError):
        validate_statement([Statement()])


# Test validate_statements minimum length requirement
@given(st.integers(min_value=-10, max_value=10))
def test_validate_statements_length_requirement(num_statements):
    """Test that validate_statements enforces minimum of 2 statements"""
    
    statements = [Statement() for _ in range(max(0, num_statements))]
    
    if num_statements >= 2:
        result = validate_statements(statements)
        assert result == statements
        assert len(result) >= 2
    else:
        with pytest.raises(TypeError) as exc_info:
            validate_statements(statements)
        assert "Statements must be a list of at least 2 Statement elements" in str(exc_info.value)


# Test custom response bodies with empty dict
def test_validate_custom_response_bodies_empty_dict():
    """Test that empty dict is accepted by validate_custom_response_bodies"""
    
    # Empty dict should be valid
    result = validate_custom_response_bodies({})
    assert result == {}


# Test custom response bodies with special keys
@given(st.dictionaries(
    st.sampled_from(["", "\x00", "key with spaces", "🔥", "__proto__", "constructor"]),
    st.none(),
    min_size=1,
    max_size=1
))
def test_custom_response_bodies_special_keys(bodies_dict):
    """Test validate_custom_response_bodies with special dictionary keys"""
    
    # Create CustomResponseBody for each key
    bodies = {}
    for key in bodies_dict:
        body = CustomResponseBody(
            Content="test",
            ContentType="TEXT_PLAIN"
        )
        bodies[key] = body
    
    # Should accept any string key with valid CustomResponseBody value
    result = validate_custom_response_bodies(bodies)
    assert result == bodies


# Property: All valid transformation types should be accepted
def test_all_valid_transformation_types_accepted():
    """Ensure all documented valid transformation types are accepted"""
    
    valid_types = [
        "BASE64_DECODE", "BASE64_DECODE_EXT", "CMD_LINE", "COMPRESS_WHITE_SPACE",
        "CSS_DECODE", "ESCAPE_SEQ_DECODE", "HEX_DECODE", "HTML_ENTITY_DECODE",
        "JS_DECODE", "LOWERCASE", "MD5", "NONE", "NORMALIZE_PATH",
        "NORMALIZE_PATH_WIN", "REMOVE_NULLS", "REPLACE_COMMENTS", "REPLACE_NULLS",
        "SQL_HEX_DECODE", "URL_DECODE", "URL_DECODE_UNI", "UTF8_TO_UNICODE"
    ]
    
    for valid_type in valid_types:
        result = validate_transformation_type(valid_type)
        assert result == valid_type


# Property: Content length boundary is inclusive at 10240
def test_content_length_boundary_inclusive():
    """Test that exactly 10240 characters is accepted"""
    
    content_10240 = "a" * 10240
    result = wafv2_custom_body_response_content(content_10240)
    assert result == content_10240
    assert len(result) == 10240
    
    content_10241 = "a" * 10241
    with pytest.raises(ValueError) as exc_info:
        wafv2_custom_body_response_content(content_10241)
    assert "Content maximum length must not exceed 10240" in str(exc_info.value)


# Test that error messages are consistent
@given(st.text(min_size=1).filter(lambda x: x not in ["IPV4", "IPV6"]))
@settings(max_examples=50)
def test_error_message_consistency(invalid_value):
    """Test that error messages follow consistent format"""
    
    with pytest.raises(ValueError) as exc_info:
        validate_ipaddress_version(invalid_value)
    
    error_msg = str(exc_info.value)
    assert "IPSet IPAddressVersion must be one of:" in error_msg
    assert "IPV4" in error_msg
    assert "IPV6" in error_msg


# Test boolean inputs (common mistake)
@given(st.booleans())
def test_validators_reject_booleans(value):
    """Test that validators properly reject boolean inputs"""
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_transformation_type(value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_comparison_operator(value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_ipaddress_version(value)


# Test with byte strings
@given(st.binary(min_size=1, max_size=10))
def test_validators_with_bytes(byte_value):
    """Test validator behavior with byte strings"""
    
    # Most validators should reject bytes
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_transformation_type(byte_value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_comparison_operator(byte_value)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_ipaddress_version(byte_value)


# Property test for idempotence - calling validator twice should give same result
@given(st.sampled_from(["IPV4", "IPV6"]))
def test_validator_idempotence(value):
    """Test that calling validator multiple times gives same result"""
    
    result1 = validate_ipaddress_version(value)
    result2 = validate_ipaddress_version(result1)
    result3 = validate_ipaddress_version(result2)
    
    assert result1 == value
    assert result2 == value
    assert result3 == value


# Test content with various unicode normalization forms
@given(st.text(alphabet="áéíóú", min_size=1, max_size=100))
def test_content_unicode_normalization(text):
    """Test content validation with unicode characters"""
    
    import unicodedata
    
    # Try different normalization forms
    nfc = unicodedata.normalize('NFC', text)
    nfd = unicodedata.normalize('NFD', text)
    
    # Both should be accepted if under length limit
    if len(nfc) <= 10240:
        result_nfc = wafv2_custom_body_response_content(nfc)
        assert result_nfc == nfc
    
    if len(nfd) <= 10240:
        result_nfd = wafv2_custom_body_response_content(nfd)
        assert result_nfd == nfd