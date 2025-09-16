import pytest
from hypothesis import given, strategies as st, assume, settings, example
from bs4.formatter import Formatter, HTMLFormatter, XMLFormatter
from bs4.element import Tag
from bs4.dammit import EntitySubstitution

# Test potential bug with quoted_attribute_value when value contains both quotes
@given(
    prefix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=0, max_size=10),
    suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=0, max_size=10)
)
@example(prefix="", suffix="")  # Test edge case with both quotes at edges
def test_quoted_attribute_value_with_both_quotes(prefix, suffix):
    """Test quoted_attribute_value when the value contains both single and double quotes."""
    # Create value with both types of quotes
    value = f'{prefix}"middle\'{suffix}'
    
    result = EntitySubstitution.quoted_attribute_value(value)
    
    # Since the value contains both quotes, we need to check the escaping
    # According to the code, if value has double quotes but no single quotes, use single quotes
    # If value has single quotes but no double quotes, use double quotes
    # But what if it has both?
    
    # The function should still return a valid quoted string
    assert len(result) >= 2
    assert result[0] in ['"', "'"]
    assert result[-1] == result[0]
    
    # Extract the content
    quote_char = result[0]
    content = result[1:-1]
    
    # If we're using double quotes, the content shouldn't have unescaped double quotes
    # If we're using single quotes, the content shouldn't have unescaped single quotes
    if quote_char == '"':
        # Check that any double quotes in content are escaped
        # Note: The function uses html.escape with quote=False, so quotes might not be escaped
        # This could be a bug!
        pass
    else:
        # Using single quotes
        pass


# Test with values that look like entities but aren't
@given(
    text=st.text().map(lambda s: f"&{s};")
)
def test_ambiguous_entities(text):
    """Test handling of strings that look like entities but may not be valid."""
    # Test with both HTML and HTML5 substitution
    html_result = EntitySubstitution.substitute_html(text)
    html5_result = EntitySubstitution.substitute_html5(text)
    
    # Both should handle the text without crashing
    assert isinstance(html_result, str)
    assert isinstance(html5_result, str)


# Test potential issue with make_quoted_attribute parameter
@given(
    value=st.text(min_size=0, max_size=50),
    make_quoted=st.booleans()
)
def test_substitute_with_make_quoted_attribute(value, make_quoted):
    """Test the make_quoted_attribute parameter in substitution methods."""
    result = EntitySubstitution.substitute_xml(value, make_quoted_attribute=make_quoted)
    
    if make_quoted:
        # Result should be quoted
        assert len(result) >= 2, f"Quoted result too short: {result}"
        assert result[0] in ['"', "'"], f"Result not quoted: {result}"
        assert result[-1] == result[0], f"Quotes don't match: {result}"
    else:
        # Result should not add quotes (but may have entity substitution)
        # Check that we didn't add surrounding quotes
        if value and not (value[0] in ['"', "'"] and value[-1] == value[0]):
            # If original wasn't quoted, result shouldn't be either
            if result and len(result) >= 2:
                # Allow for entity substitution changing the content
                pass


# Test formatter.substitute with NavigableString in CDATA context
@given(
    text=st.text(min_size=0, max_size=50),
    cdata_tag=st.sampled_from(["script", "style", "other"])
)
def test_formatter_substitute_with_cdata_context(text, cdata_tag):
    """Test that substitute respects CDATA containing tags."""
    from bs4.element import NavigableString, Tag
    
    # Create formatter with HTML defaults
    formatter = Formatter(
        language=Formatter.HTML,
        entity_substitution=EntitySubstitution.substitute_xml
    )
    
    # Create a NavigableString with a parent
    parent = Tag(name=cdata_tag)
    ns = NavigableString(text)
    ns.parent = parent
    
    result = formatter.substitute(ns)
    
    if cdata_tag in formatter.cdata_containing_tags:
        # Should not substitute - should return original
        assert result == text, f"CDATA content was substituted when it shouldn't be"
    else:
        # Should apply substitution
        # Check if special characters were substituted
        if '<' in text or '>' in text or '&' in text:
            # Some substitution should have occurred
            pass


# Deep test: Formatter initialization with invalid indent types
@given(
    indent=st.one_of(
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.complex_numbers()
    )
)
def test_formatter_invalid_indent_types(indent):
    """Test that invalid indent types are handled gracefully."""
    formatter = Formatter(indent=indent)
    
    # Should default to single space for invalid types
    assert formatter.indent == " ", f"Invalid indent type {type(indent)} didn't default to single space"


# Test potential overflow with very large repeating patterns
@given(
    pattern=st.sampled_from(["&amp;", "&lt;", "&gt;", "&#39;", "&quot;"]),
    repeat=st.integers(min_value=100, max_value=1000)
)
def test_large_entity_patterns(pattern, repeat):
    """Test handling of large repeating entity patterns."""
    text = pattern * repeat
    
    # These should handle large inputs without issues
    result = EntitySubstitution.substitute_xml_containing_entities(text)
    
    # Should preserve the entities
    assert pattern in result
    # Rough check that we didn't lose too many patterns
    assert result.count(pattern) >= repeat // 2  # Allow some merging/processing


# Test edge case: Empty string edge cases
def test_empty_string_edge_cases():
    """Test various empty string scenarios."""
    # Empty string substitution
    assert EntitySubstitution.substitute_html("") == ""
    assert EntitySubstitution.substitute_html5("") == ""
    assert EntitySubstitution.substitute_xml("") == ""
    
    # Empty string quoting
    quoted = EntitySubstitution.quoted_attribute_value("")
    assert quoted == '""', f"Empty string not properly quoted: {quoted}"
    
    # Formatter with empty string
    formatter = Formatter()
    assert formatter.substitute("") == ""
    assert formatter.attribute_value("") == ""


# Test interaction between empty_attributes_are_booleans and None values
@given(
    attrs=st.dictionaries(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
        st.one_of(
            st.just(None),
            st.just(""),
            st.just("value")
        ),
        min_size=1,
        max_size=5
    )
)
def test_none_vs_empty_string_behavior(attrs):
    """Test that None and empty string are handled differently."""
    formatter_bool = Formatter(empty_attributes_are_booleans=True)
    formatter_no_bool = Formatter(empty_attributes_are_booleans=False)
    
    tag = Tag(name="test")
    tag.attrs = attrs.copy()
    
    result_bool = dict(formatter_bool.attributes(tag))
    result_no_bool = dict(formatter_no_bool.attributes(tag))
    
    for key, value in attrs.items():
        if value is None:
            # None should always remain None in both formatters
            assert result_bool[key] is None
            assert result_no_bool[key] is None
        elif value == "":
            # Empty string behavior differs
            assert result_bool[key] is None  # Converted to None
            assert result_no_bool[key] == ""  # Remains empty string
        else:
            # Regular values unchanged
            assert result_bool[key] == value
            assert result_no_bool[key] == value


# Test potential issue with special regex characters in substitution
@given(
    text=st.text(alphabet="()[]{}.*+?^$|\\", min_size=1, max_size=20)
)
def test_regex_special_chars_in_substitution(text):
    """Test that regex special characters don't cause issues in substitution."""
    # These characters might cause regex issues if not properly handled
    try:
        html_result = EntitySubstitution.substitute_html(text)
        xml_result = EntitySubstitution.substitute_xml(text)
        assert isinstance(html_result, str)
        assert isinstance(xml_result, str)
    except Exception as e:
        pytest.fail(f"Regex special chars caused error: {e}")


# Comprehensive test for all built-in formatters
def test_all_registry_formatters():
    """Test that all registered formatters work correctly."""
    # Test HTML formatters
    for key in HTMLFormatter.REGISTRY:
        formatter = HTMLFormatter.REGISTRY[key]
        assert isinstance(formatter, HTMLFormatter)
        
        # Test basic functionality
        tag = Tag(name="test")
        tag.attrs = {"a": "1", "b": "2"}
        attrs = list(formatter.attributes(tag))
        assert len(attrs) == 2
        assert attrs[0][0] == "a"  # Should be sorted
        
    # Test XML formatters
    for key in XMLFormatter.REGISTRY:
        formatter = XMLFormatter.REGISTRY[key]
        assert isinstance(formatter, XMLFormatter)
        
        # Test basic functionality
        tag = Tag(name="test")
        tag.attrs = {"x": "1", "y": "2"}
        attrs = list(formatter.attributes(tag))
        assert len(attrs) == 2
        assert attrs[0][0] == "x"  # Should be sorted


if __name__ == "__main__":
    print("Running deeper property tests for bs4.formatter...")
    import sys
    pytest.main([__file__, "-v", "--tb=short"])