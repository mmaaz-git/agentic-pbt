#!/usr/bin/env python3
"""Property-based tests for lxml.isoschematron module."""

import sys
from hypothesis import given, strategies as st, assume, settings
from lxml import etree
import lxml.isoschematron as iso

# Test 1: stylesheet_params handles empty values
@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.text(min_size=0),  # Include empty strings
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans()
    ),
    min_size=0,
    max_size=10
))
def test_stylesheet_params_empty_string_handling(params):
    """Test that stylesheet_params properly handles empty string values."""
    # Filter out None values since they're not allowed
    filtered_params = {k: v for k, v in params.items() if v is not None}
    
    result = iso.stylesheet_params(**filtered_params)
    
    # All keys should be preserved
    assert set(result.keys()) == set(filtered_params.keys())
    
    # Empty strings should be wrapped but still "exist"
    for key, value in filtered_params.items():
        assert key in result
        if isinstance(value, str):
            # String values should be wrapped in _XSLTQuotedStringParam
            assert isinstance(result[key], etree._XSLTQuotedStringParam)
        else:
            # Non-string values should be converted to unicode/string
            assert isinstance(result[key], str)


# Test 2: _stylesheet_param_dict None handling inconsistency
@given(
    st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers())),
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.text(), st.integers(), st.none())
    )
)
def test_stylesheet_param_dict_none_override(base_dict, kwargs_dict):
    """Test that _stylesheet_param_dict properly filters None values."""
    result = iso._stylesheet_param_dict(base_dict, kwargs_dict)
    
    # None values in kwargs_dict should not override base_dict
    for key, value in kwargs_dict.items():
        if value is None and key in base_dict:
            # The base value should be preserved
            assert key in result
        elif value is not None:
            # Non-None values should override
            assert key in result


# Test 3: Empty value inconsistency bug
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.text(min_size=0, max_size=100),  # Include empty strings
    min_size=1,
    max_size=5
))
def test_stylesheet_params_empty_value_bug(params):
    """Test for potential bug with empty string values in stylesheet_params."""
    result = iso.stylesheet_params(**params)
    
    # Check if empty strings cause issues
    for key, value in params.items():
        if value == "":
            # Empty string should still be wrapped and present
            assert key in result
            assert isinstance(result[key], etree._XSLTQuotedStringParam)


# Test 4: Check for XPath injection in stylesheet_params
@given(st.text(min_size=0))
def test_stylesheet_params_xpath_injection(value):
    """Test that special XPath characters are properly escaped."""
    # Test with potentially dangerous XPath strings
    dangerous_strings = [
        "'; DROP TABLE users; --",
        "' or '1'='1",
        "../../etc/passwd",
        "<script>alert('xss')</script>",
        "\" or \"1\"=\"1"
    ]
    
    for dangerous in dangerous_strings:
        result = iso.stylesheet_params(test=dangerous)
        # Should be safely wrapped
        assert 'test' in result
        assert isinstance(result['test'], etree._XSLTQuotedStringParam)


# Test 5: Schematron validation with empty/minimal documents
@given(st.one_of(
    st.just(""),  # Empty string
    st.just("<root/>"),  # Minimal XML
    st.just("<root></root>"),  # Empty element
))
def test_schematron_empty_document_validation(xml_string):
    """Test Schematron validation with edge case documents."""
    # Create a minimal schematron that should pass for any document
    schema_xml = """
    <schema xmlns="http://purl.oclc.org/dsdl/schematron">
        <pattern>
            <rule context="*">
                <assert test="true()">Always passes</assert>
            </rule>
        </pattern>
    </schema>
    """
    
    try:
        schema_doc = etree.XML(schema_xml)
        schematron = iso.Schematron(schema_doc)
        
        if xml_string:
            doc = etree.XML(xml_string)
            result = schematron.validate(doc)
            # Should always pass with our permissive schema
            assert result is True
    except etree.XMLSyntaxError:
        # Empty string will cause XMLSyntaxError, which is expected
        if xml_string != "":
            raise


# Test 6: Test for empty key handling in stylesheet_params
@given(st.dictionaries(
    st.text(min_size=0, max_size=20),  # Allow empty keys
    st.one_of(st.text(), st.integers()),
    min_size=0,
    max_size=5
))
def test_stylesheet_params_empty_key_bug(params):
    """Test if empty string keys cause issues in stylesheet_params."""
    # Filter out empty keys as they might not be valid Python kwargs
    if "" in params:
        # Empty string as key should cause issues in Python kwargs
        try:
            result = iso.stylesheet_params(**params)
            # If it works, empty key should be preserved
            if "" in params:
                assert "" in result
        except (TypeError, SyntaxError):
            # Expected - empty string is not a valid kwarg name
            pass
    else:
        result = iso.stylesheet_params(**params)
        assert set(result.keys()) == set(params.keys())


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])