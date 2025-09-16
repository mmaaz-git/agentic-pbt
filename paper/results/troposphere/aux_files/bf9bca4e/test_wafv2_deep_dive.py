"""Deep dive tests to find edge cases and potential bugs in troposphere.wafv2"""

import pytest
from hypothesis import given, strategies as st, settings, assume
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


# Test for potential type coercion issues
def test_type_coercion_issues():
    """Test if validators handle type coercion correctly"""
    
    # Test with integer 0 (might be confused with False or empty)
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_transformation_type(0)
    
    # Test with float that looks like a valid option
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_comparison_operator(1.0)  
    
    # Test with boolean True/False
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_ipaddress_version(True)
    
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_ipaddress_version(False)


# Test content validation with exactly 1 character (boundary)
def test_content_single_character():
    """Test that single character content is accepted"""
    
    result = wafv2_custom_body_response_content("a")
    assert result == "a"
    assert len(result) == 1


# Test content with null bytes
def test_content_with_null_bytes():
    """Test content validation with null bytes"""
    
    # Content with null byte in middle
    content = "hello\x00world"
    result = wafv2_custom_body_response_content(content)
    assert result == content
    
    # Content that's just a null byte
    content = "\x00"
    result = wafv2_custom_body_response_content(content)
    assert result == content
    
    # Multiple null bytes
    content = "\x00" * 100
    result = wafv2_custom_body_response_content(content)
    assert result == content


# Test validators with substrings of valid values
@given(st.sampled_from(["IPV", "V4", "IP", "PV4", "IPV", "6", "V6", "PV6"]))
def test_validators_reject_substrings_of_valid_values(substring):
    """Test that validators don't accept substrings of valid values"""
    
    with pytest.raises(ValueError):
        validate_ipaddress_version(substring)


# Test validators with concatenated valid values
def test_validators_reject_concatenated_valid_values():
    """Test that validators don't accept concatenated valid values"""
    
    # "IPV4IPV6" should not be valid
    with pytest.raises(ValueError):
        validate_ipaddress_version("IPV4IPV6")
    
    # "EQNE" should not be valid
    with pytest.raises(ValueError):
        validate_comparison_operator("EQNE")
    
    # Multiple valid values concatenated
    with pytest.raises(ValueError):
        validate_transformation_type("LOWERCASEMD5NONE")


# Test with strings that contain valid values
def test_validators_reject_strings_containing_valid_values():
    """Test that validators require exact matches, not contains"""
    
    # Should reject strings that contain but aren't exactly the valid value
    with pytest.raises(ValueError):
        validate_ipaddress_version("IPV4_VERSION")
    
    with pytest.raises(ValueError):
        validate_ipaddress_version("USE_IPV4")
    
    with pytest.raises(ValueError):
        validate_comparison_operator("EQ_OPERATOR")
    
    with pytest.raises(ValueError):
        validate_transformation_type("NONE_TYPE")


# Test special string inputs
@given(st.sampled_from(["", " ", "\t", "\n", "\r", "\\n", "\\t", "\\r"]))
def test_validators_with_special_strings(special_str):
    """Test validators with various special string inputs"""
    
    # All should be rejected
    with pytest.raises(ValueError):
        validate_transformation_type(special_str)
    
    with pytest.raises(ValueError):
        validate_comparison_operator(special_str)
    
    with pytest.raises(ValueError):
        validate_ipaddress_version(special_str)


# Test content type with wrong case
def test_content_type_case_sensitivity():
    """Test that content type validator is strictly case-sensitive"""
    
    # Valid types
    assert wafv2_custom_body_response_content_type("APPLICATION_JSON") == "APPLICATION_JSON"
    assert wafv2_custom_body_response_content_type("TEXT_HTML") == "TEXT_HTML"
    assert wafv2_custom_body_response_content_type("TEXT_PLAIN") == "TEXT_PLAIN"
    
    # Invalid due to case
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content_type("application_json")
    
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content_type("Application_Json")
    
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content_type("text_html")
    
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content_type("Text_Plain")


# Test validate_statements with exactly 2 statements (boundary)
def test_validate_statements_exactly_two():
    """Test that exactly 2 statements is accepted"""
    
    statements = [Statement(), Statement()]
    result = validate_statements(statements)
    assert result == statements
    assert len(result) == 2


# Test validate_statements with 1 statement (should fail)
def test_validate_statements_single_statement():
    """Test that single statement is rejected"""
    
    statements = [Statement()]
    with pytest.raises(TypeError) as exc_info:
        validate_statements(statements)
    assert "Statements must be a list of at least 2 Statement elements" in str(exc_info.value)


# Test validate_statements with empty list
def test_validate_statements_empty_list():
    """Test that empty list is rejected"""
    
    statements = []
    with pytest.raises(TypeError) as exc_info:
        validate_statements(statements)
    assert "Statements must be a list of at least 2 Statement elements" in str(exc_info.value)


# Test validate_statements with mixed valid and invalid items
def test_validate_statements_mixed_items():
    """Test validate_statements with mixed valid and invalid items"""
    
    # List with one Statement and one non-Statement
    mixed = [Statement(), "not a statement"]
    
    with pytest.raises(TypeError):
        validate_statements(mixed)


# Test custom response bodies with None values in dict
def test_custom_response_bodies_none_values():
    """Test validate_custom_response_bodies with None as value"""
    
    bodies = {"key": None}
    
    with pytest.raises(ValueError) as exc_info:
        validate_custom_response_bodies(bodies)
    assert "must be type of CustomResponseBody" in str(exc_info.value)


# Test transformation types that are similar but not exact
@given(st.sampled_from([
    "BASE_64_DECODE",  # Should be BASE64_DECODE
    "BASE64DECODE",    # Should be BASE64_DECODE
    "base64_decode",   # Should be BASE64_DECODE
    "CMDLINE",         # Should be CMD_LINE
    "HTMLENTITYDECODE", # Should be HTML_ENTITY_DECODE
    "JSDECODE",        # Should be JS_DECODE
    "SQLDECODE",       # Should be SQL_HEX_DECODE
]))
def test_transformation_type_similar_but_wrong(value):
    """Test that similar but incorrect transformation types are rejected"""
    
    with pytest.raises(ValueError):
        validate_transformation_type(value)


# Test for off-by-one errors in content length
@given(st.sampled_from([10239, 10240, 10241, 10242]))
def test_content_length_off_by_one(length):
    """Test potential off-by-one errors in content length validation"""
    
    content = "x" * length
    
    if length <= 10240:
        result = wafv2_custom_body_response_content(content)
        assert result == content
        assert len(result) == length
    else:
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content maximum length must not exceed 10240" in str(exc_info.value)


# Test validators preserve input exactly when valid
@given(st.sampled_from(["IPV4", "IPV6"]))
def test_validators_preserve_exact_input(value):
    """Test that validators return the exact input string when valid"""
    
    result = validate_ipaddress_version(value)
    assert result is value  # Should be the same object
    assert id(result) == id(value)  # Same memory address


# Test content with exactly maximum length
def test_content_exactly_max_length():
    """Test content with exactly the maximum allowed length"""
    
    max_content = "a" * 10240
    result = wafv2_custom_body_response_content(max_content)
    assert result == max_content
    assert len(result) == 10240
    
    # One more character should fail
    over_max = "a" * 10241
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content(over_max)