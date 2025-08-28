"""Property-based tests for troposphere.wafv2 validation functions"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from troposphere.validators.wafv2 import (
    validate_transformation_type,
    validate_comparison_operator,
    validate_ipaddress_version,
    validate_positional_constraint,
    validate_statements,
    validate_statement,
    wafv2_custom_body_response_content,
    wafv2_custom_body_response_content_type,
    validate_custom_response_bodies,
)
from troposphere import AWSHelperFn
from troposphere.wafv2 import Statement, CustomResponseBody


# Test 1: validate_transformation_type whitelist validation
@given(st.text())
def test_validate_transformation_type_accepts_only_valid_types(transformation):
    VALID_TYPES = {
        "BASE64_DECODE", "BASE64_DECODE_EXT", "CMD_LINE", "COMPRESS_WHITE_SPACE",
        "CSS_DECODE", "ESCAPE_SEQ_DECODE", "HEX_DECODE", "HTML_ENTITY_DECODE",
        "JS_DECODE", "LOWERCASE", "MD5", "NONE", "NORMALIZE_PATH",
        "NORMALIZE_PATH_WIN", "REMOVE_NULLS", "REPLACE_COMMENTS", "REPLACE_NULLS",
        "SQL_HEX_DECODE", "URL_DECODE", "URL_DECODE_UNI", "UTF8_TO_UNICODE"
    }
    
    if transformation in VALID_TYPES:
        # Should accept valid types
        result = validate_transformation_type(transformation)
        assert result == transformation
    else:
        # Should reject invalid types
        with pytest.raises(ValueError) as exc_info:
            validate_transformation_type(transformation)
        assert "WebACL TextTransformation must be one of" in str(exc_info.value)


# Test 2: validate_comparison_operator whitelist validation
@given(st.text())
def test_validate_comparison_operator_accepts_only_valid_operators(operator):
    VALID_OPERATORS = {"EQ", "GE", "GT", "LE", "LT", "NE"}
    
    if operator in VALID_OPERATORS:
        result = validate_comparison_operator(operator)
        assert result == operator
    else:
        with pytest.raises(ValueError) as exc_info:
            validate_comparison_operator(operator)
        assert "WebACL SizeConstraintStatement must be one of" in str(exc_info.value)


# Test 3: validate_ipaddress_version whitelist validation
@given(st.text())
def test_validate_ipaddress_version_accepts_only_valid_versions(version):
    VALID_VERSIONS = {"IPV4", "IPV6"}
    
    if version in VALID_VERSIONS:
        result = validate_ipaddress_version(version)
        assert result == version
    else:
        with pytest.raises(ValueError) as exc_info:
            validate_ipaddress_version(version)
        assert "IPSet IPAddressVersion must be one of" in str(exc_info.value)


# Test 4: validate_positional_constraint whitelist validation
@given(st.text())
def test_validate_positional_constraint_accepts_only_valid_constraints(constraint):
    VALID_CONSTRAINTS = {"CONTAINS", "CONTAINS_WORD", "ENDS_WITH", "EXACTLY", "STARTS_WITH"}
    
    if constraint in VALID_CONSTRAINTS:
        result = validate_positional_constraint(constraint)
        assert result == constraint
    else:
        with pytest.raises(ValueError) as exc_info:
            validate_positional_constraint(constraint)
        assert "ByteMatchStatement PositionalConstraint must be one of" in str(exc_info.value)


# Test 5: wafv2_custom_body_response_content length bounds
@given(st.text(min_size=0, max_size=20000))
def test_custom_body_response_content_length_bounds(content):
    content_length = len(content)
    
    if content_length == 0:
        # Empty content should be rejected
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content must not be empty" in str(exc_info.value)
    elif content_length > 10240:
        # Content > 10240 chars should be rejected
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content maximum length must not exceed 10240" in str(exc_info.value)
    else:
        # Valid length content should be accepted
        result = wafv2_custom_body_response_content(content)
        assert result == content


# Test 6: Edge case - exact boundary of 10240 characters
@given(st.integers(min_value=10230, max_value=10250))
def test_custom_body_response_content_exact_boundary(length):
    content = "a" * length
    
    if length <= 10240:
        result = wafv2_custom_body_response_content(content)
        assert result == content
    else:
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content(content)
        assert "Content maximum length must not exceed 10240" in str(exc_info.value)


# Test 7: wafv2_custom_body_response_content_type whitelist validation
@given(st.text())
def test_custom_body_response_content_type_accepts_only_valid_types(content_type):
    VALID_TYPES = {"APPLICATION_JSON", "TEXT_HTML", "TEXT_PLAIN"}
    
    if content_type in VALID_TYPES:
        result = wafv2_custom_body_response_content_type(content_type)
        assert result == content_type
    else:
        with pytest.raises(ValueError) as exc_info:
            wafv2_custom_body_response_content_type(content_type)
        assert "ContentType must be one of" in str(exc_info.value)


# Test 8: validate_statements list requirements
@given(st.lists(st.none(), min_size=0, max_size=5))
def test_validate_statements_requires_list_of_at_least_2(statements_list):
    # Create mock Statement objects
    mock_statements = []
    for _ in statements_list:
        stmt = Statement()
        mock_statements.append(stmt)
    
    if len(mock_statements) >= 2:
        result = validate_statements(mock_statements)
        assert result == mock_statements
    else:
        with pytest.raises(TypeError) as exc_info:
            validate_statements(mock_statements)
        assert "Statements must be a list of at least 2 Statement elements" in str(exc_info.value)


# Test 9: validate_statements rejects non-lists
@given(st.one_of(st.text(), st.integers(), st.dictionaries(st.text(), st.text())))
def test_validate_statements_rejects_non_lists(statements):
    with pytest.raises(TypeError) as exc_info:
        validate_statements(statements)
    assert "Statements must be a list of at least 2 Statement elements" in str(exc_info.value)


# Test 10: validate_custom_response_bodies type validation
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.text(), st.integers(), st.none()),
    min_size=0,
    max_size=5
))
def test_validate_custom_response_bodies_requires_dict_with_correct_values(bodies):
    # Test with non-CustomResponseBody values
    should_fail = False
    for v in bodies.values():
        if not isinstance(v, CustomResponseBody):
            should_fail = True
            break
    
    if should_fail:
        with pytest.raises(ValueError) as exc_info:
            validate_custom_response_bodies(bodies)
        assert "must be type of CustomResponseBody" in str(exc_info.value)
    else:
        # Empty dict should pass
        if len(bodies) == 0:
            result = validate_custom_response_bodies(bodies)
            assert result == bodies


# Test 11: validate_custom_response_bodies accepts valid CustomResponseBody
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.just(None),
    min_size=1,
    max_size=3
))
def test_validate_custom_response_bodies_with_valid_objects(keys_dict):
    bodies = {}
    for key in keys_dict:
        # Create valid CustomResponseBody
        body = CustomResponseBody(
            Content="test content",
            ContentType="TEXT_PLAIN"
        )
        bodies[key] = body
    
    result = validate_custom_response_bodies(bodies)
    assert result == bodies


# Test 12: Case sensitivity for all whitelist validators
def test_case_sensitivity_of_validators():
    # Test transformation type is case-sensitive
    with pytest.raises(ValueError):
        validate_transformation_type("lowercase")  # Should be "LOWERCASE"
    
    # Test comparison operator is case-sensitive
    with pytest.raises(ValueError):
        validate_comparison_operator("eq")  # Should be "EQ"
    
    # Test IP version is case-sensitive
    with pytest.raises(ValueError):
        validate_ipaddress_version("ipv4")  # Should be "IPV4"
    
    # Test positional constraint is case-sensitive
    with pytest.raises(ValueError):
        validate_positional_constraint("contains")  # Should be "CONTAINS"
    
    # Test content type is case-sensitive
    with pytest.raises(ValueError):
        wafv2_custom_body_response_content_type("text_plain")  # Should be "TEXT_PLAIN"