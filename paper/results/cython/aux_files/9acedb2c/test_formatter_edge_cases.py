import pytest
from hypothesis import given, strategies as st, assume, settings, example
from bs4.formatter import Formatter, HTMLFormatter, XMLFormatter
from bs4.element import Tag
from bs4.dammit import EntitySubstitution
import html

# Test for quoted_attribute_value edge cases
@given(
    value=st.text(min_size=0, max_size=100)
)
def test_quoted_attribute_value_always_returns_quoted(value):
    """Test that quoted_attribute_value always returns a properly quoted string."""
    result = EntitySubstitution.quoted_attribute_value(value)
    
    # Property: Result should always start and end with a quote character
    assert len(result) >= 2, f"Result too short: {result}"
    assert result[0] in ['"', "'"], f"Result doesn't start with quote: {result}"
    assert result[-1] in ['"', "'"], f"Result doesn't end with quote: {result}"
    assert result[0] == result[-1], f"Start and end quotes don't match: {result}"
    
    # Property: The original value should be contained within the quotes
    unquoted = result[1:-1]
    
    # If we used single quotes, there should be no unescaped single quotes in the value
    if result[0] == "'":
        assert "'" not in value, f"Single quote used but value contains single quote: {value}"
    
    # If we used double quotes, there should be no unescaped double quotes in the value  
    if result[0] == '"':
        assert '"' not in value, f"Double quote used but value contains double quote: {value}"


# Test substitute_html5_raw with ambiguous ampersands
@given(
    entity_name=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20)
)
def test_substitute_html5_raw_escapes_unknown_entities(entity_name):
    """Test that substitute_html5_raw properly escapes unknown entities."""
    # Create an unknown entity reference
    text = f"&{entity_name};"
    
    result = EntitySubstitution.substitute_html5_raw(text)
    
    # Check if this is a known entity
    from html import entities
    if entity_name in entities.name2codepoint or entity_name in EntitySubstitution.HTML_ENTITY_TO_CHARACTER:
        # Known entity - might be preserved or converted
        pass
    else:
        # Unknown entity - should be escaped
        # The ampersand should be escaped to &amp;
        assert result == f"&amp;{entity_name};", \
            f"Unknown entity &{entity_name}; not properly escaped: {result}"


# Test edge case with empty Tag attrs
@given(
    name=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10)
)
def test_formatter_handles_none_attrs(name):
    """Test that formatter handles tags with None attrs gracefully."""
    formatter = Formatter()
    tag = Tag(name=name)
    tag.attrs = None
    
    result = list(formatter.attributes(tag))
    assert result == [], f"None attrs should return empty list, got {result}"


# Test very large indent values
@given(
    indent=st.integers(min_value=100, max_value=1000)
)
def test_formatter_large_indent(indent):
    """Test that large indent values don't cause issues."""
    formatter = Formatter(indent=indent)
    assert formatter.indent == " " * indent
    assert len(formatter.indent) == indent


# Test substitute methods with strings containing only entities
@given(
    entities=st.lists(
        st.sampled_from(["&lt;", "&gt;", "&amp;", "&quot;", "&apos;", "&#39;", "&#x27;"]),
        min_size=1,
        max_size=10
    )
)
def test_substitute_preserves_valid_entities(entities):
    """Test that valid entities are preserved correctly."""
    text = "".join(entities)
    
    # substitute_xml_containing_entities should preserve these
    result = EntitySubstitution.substitute_xml_containing_entities(text)
    
    # All original entities should still be present
    for entity in entities:
        assert entity in result, f"Entity {entity} lost in substitution"


# Test formatter with mixed language settings
@given(
    base_language=st.sampled_from([Formatter.HTML, Formatter.XML]),
    override_cdata=st.one_of(st.none(), st.sets(st.text(min_size=1, max_size=5), max_size=3))
)
def test_formatter_language_override(base_language, override_cdata):
    """Test that explicit cdata_containing_tags overrides language defaults."""
    formatter = Formatter(language=base_language, cdata_containing_tags=override_cdata)
    
    if override_cdata is not None:
        assert formatter.cdata_containing_tags == override_cdata, \
            f"Explicit cdata_containing_tags not respected"
    else:
        if base_language == Formatter.XML:
            assert formatter.cdata_containing_tags == set()
        else:
            assert formatter.cdata_containing_tags == set(["script", "style"])


# Test attribute sorting with special characters
@given(
    attrs=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda x: x[0].isalpha()),
        st.text(min_size=0, max_size=50),
        min_size=2,
        max_size=10
    )
)
def test_attributes_sorting_stability(attrs):
    """Test that attribute sorting is stable and consistent."""
    formatter = Formatter()
    tag = Tag(name="test")
    tag.attrs = attrs
    
    # Get attributes multiple times
    result1 = list(formatter.attributes(tag))
    result2 = list(formatter.attributes(tag))
    result3 = list(formatter.attributes(tag))
    
    # Should always return the same result
    assert result1 == result2 == result3, "Attribute sorting not stable"
    
    # Keys should be sorted
    keys = [k for k, v in result1]
    assert keys == sorted(keys)


# Test entity substitution with Unicode characters
@given(
    text=st.text(
        alphabet=st.characters(min_codepoint=128, max_codepoint=0x10000),
        min_size=0,
        max_size=20
    )
)
def test_unicode_substitution(text):
    """Test that Unicode characters are handled correctly in substitution."""
    # This should not crash
    html_result = EntitySubstitution.substitute_html(text)
    html5_result = EntitySubstitution.substitute_html5(text)
    xml_result = EntitySubstitution.substitute_xml(text)
    
    # Basic sanity checks
    assert isinstance(html_result, str)
    assert isinstance(html5_result, str)
    assert isinstance(xml_result, str)


# Test formatter substitution with None entity_substitution
@given(
    text=st.text(min_size=0, max_size=50)
)
def test_formatter_none_substitution(text):
    """Test that None entity_substitution means no substitution."""
    formatter = Formatter(entity_substitution=None)
    result = formatter.substitute(text)
    
    # With None substitution, text should be unchanged
    assert result == text, f"Text changed with None substitution: {text} -> {result}"


# Complex test: Multiple formatters with same tag
@given(
    attrs=st.dictionaries(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
        st.one_of(st.none(), st.just(""), st.text(min_size=1, max_size=20)),
        min_size=0,
        max_size=5
    )
)
def test_multiple_formatters_consistency(attrs):
    """Test that different formatters handle the same tag consistently."""
    tag = Tag(name="test")
    tag.attrs = attrs
    
    # Create different formatters
    html_formatter = HTMLFormatter()
    xml_formatter = XMLFormatter()
    minimal_formatter = Formatter(entity_substitution=EntitySubstitution.substitute_xml)
    
    # All should return sorted attributes
    html_attrs = list(html_formatter.attributes(tag))
    xml_attrs = list(xml_formatter.attributes(tag))
    minimal_attrs = list(minimal_formatter.attributes(tag))
    
    # Extract just the keys
    html_keys = [k for k, v in html_attrs]
    xml_keys = [k for k, v in xml_attrs]
    minimal_keys = [k for k, v in minimal_attrs]
    
    # All should have the same sorted keys
    assert html_keys == xml_keys == minimal_keys == sorted(attrs.keys())


# Test edge case: substitute methods with consecutive special characters
@given(
    special_chars=st.lists(
        st.sampled_from(['<', '>', '&']),
        min_size=1,
        max_size=10
    )
)
def test_consecutive_special_chars(special_chars):
    """Test substitution with consecutive special characters."""
    text = ''.join(special_chars)
    
    xml_result = EntitySubstitution.substitute_xml(text)
    
    # No unescaped special characters should remain
    assert '<' not in xml_result.replace('&lt;', '')
    assert '>' not in xml_result.replace('&gt;', '')
    
    # Count that we have the right number of substitutions
    original_lt = text.count('<')
    original_gt = text.count('>')
    result_lt = xml_result.count('&lt;')
    result_gt = xml_result.count('&gt;')
    
    assert result_lt == original_lt
    assert result_gt == original_gt


if __name__ == "__main__":
    print("Running edge case tests for bs4.formatter...")
    import sys
    pytest.main([__file__, "-v", "--tb=short"])