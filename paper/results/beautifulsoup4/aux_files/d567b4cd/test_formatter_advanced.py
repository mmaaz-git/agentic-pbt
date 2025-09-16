import pytest
from hypothesis import given, strategies as st, assume, settings
from bs4.element import Tag
from bs4.formatter import Formatter, HTMLFormatter, XMLFormatter
from bs4 import BeautifulSoup
from bs4.dammit import EntitySubstitution
import string


# Strategy for attribute values that might need entity substitution
entity_text = st.text(alphabet=string.printable, min_size=0, max_size=50)

# Strategy for formatter types
formatter_types = st.sampled_from(['html', 'html5', 'minimal', None])


@given(entity_text)
def test_attribute_value_substitution(text):
    """Test that attribute_value method correctly calls substitute."""
    formatter = HTMLFormatter(entity_substitution=EntitySubstitution.substitute_html)
    
    result = formatter.attribute_value(text)
    expected = formatter.substitute(text)
    
    assert result == expected, f"attribute_value and substitute return different results for '{text}'"


@given(st.text(alphabet="<>&\"'", min_size=1, max_size=20))
def test_entity_substitution_special_chars(text):
    """Test entity substitution with special HTML characters."""
    html_formatter = HTMLFormatter.REGISTRY['html']
    html5_formatter = HTMLFormatter.REGISTRY['html5']
    minimal_formatter = HTMLFormatter.REGISTRY['minimal']
    none_formatter = HTMLFormatter.REGISTRY[None]
    
    # None formatter should not change anything
    assert none_formatter.substitute(text) == text
    
    # HTML formatter should escape &
    if '&' in text:
        html_result = html_formatter.substitute(text)
        # Check that standalone & is escaped in html formatter
        if not any(text[i:].startswith(('&amp;', '&#', '&lt;', '&gt;', '&quot;')) for i in range(len(text)) if text[i] == '&'):
            assert '&amp;' in html_result or '&' not in html_result
    
    # Minimal formatter should handle basic XML entities
    minimal_result = minimal_formatter.substitute(text)
    if '<' in text:
        assert '&lt;' in minimal_result
    if '>' in text:
        assert '&gt;' in minimal_result


@given(st.dictionaries(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    st.text(min_size=0, max_size=10),
    min_size=1,
    max_size=5
))
@settings(max_examples=200)
def test_empty_string_attribute_edge_cases(attrs):
    """Test edge cases with empty string attributes and boolean conversion."""
    # Create formatter with empty_attributes_are_booleans=True
    formatter = Formatter(empty_attributes_are_booleans=True)
    tag = Tag(name="test")
    
    # Count how many attributes have empty string values
    empty_count = sum(1 for v in attrs.values() if v == "")
    
    # Set attributes
    for k, v in attrs.items():
        tag[k] = v
    
    # Get formatted attributes
    result = list(formatter.attributes(tag))
    
    # Count how many None values we got
    none_count = sum(1 for k, v in result if v is None)
    
    # Should match the number of empty strings
    assert none_count == empty_count, f"Expected {empty_count} None values, got {none_count}"


@given(st.one_of(
    st.just(float('inf')),
    st.just(float('-inf')),
    st.just(float('nan')),
    st.floats(),
    st.complex_numbers(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_indent_invalid_types(indent_value):
    """Test that invalid indent types fall back to default."""
    try:
        formatter = Formatter(indent=indent_value)
        # Should handle gracefully - check what it becomes
        if isinstance(indent_value, (int, float)) and not (str(indent_value) in ['inf', '-inf', 'nan']):
            if indent_value <= 0:
                assert formatter.indent == ""
            else:
                assert formatter.indent == " " * int(indent_value)
        elif isinstance(indent_value, str):
            assert formatter.indent == indent_value
        else:
            # Invalid types should default to single space
            assert formatter.indent == " "
    except (TypeError, ValueError, OverflowError):
        # Some types might raise exceptions, which is acceptable
        pass


@given(st.text(min_size=0, max_size=100))
def test_substitute_with_no_entity_function(text):
    """Test that substitute returns text unchanged when entity_substitution is None."""
    formatter = Formatter(entity_substitution=None)
    result = formatter.substitute(text)
    assert result == text, "Text changed when entity_substitution is None"


@given(st.sampled_from(['script', 'style', 'p', 'div', 'span']),
       st.text(alphabet="<>&\"'", min_size=0, max_size=50))
def test_cdata_tag_checking(tag_name, content):
    """Test that CDATA checking works correctly for different tags."""
    from bs4.element import NavigableString
    
    formatter = HTMLFormatter(entity_substitution=EntitySubstitution.substitute_html)
    
    # Create a tag and content
    tag = Tag(name=tag_name)
    nav_string = NavigableString(content)
    nav_string.parent = tag
    
    result = formatter.substitute(nav_string)
    
    if tag_name in formatter.cdata_containing_tags:
        # Should not be substituted
        assert result == content, f"Content in {tag_name} was substituted"
    else:
        # Should be substituted
        expected = EntitySubstitution.substitute_html(content)
        assert result == expected, f"Content in {tag_name} was not substituted"


@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=5), min_size=0, max_size=10))
def test_cdata_containing_tags_default(tag_list):
    """Test the default CDATA containing tags for HTML vs XML."""
    # HTML should have script and style as CDATA tags
    html_formatter = Formatter(language=Formatter.HTML)
    assert 'script' in html_formatter.cdata_containing_tags
    assert 'style' in html_formatter.cdata_containing_tags
    
    # XML should have empty set
    xml_formatter = Formatter(language=Formatter.XML)
    assert xml_formatter.cdata_containing_tags == set()
    
    # Custom tags should override
    custom_tags = set(tag_list)
    custom_formatter = Formatter(language=Formatter.HTML, cdata_containing_tags=custom_tags)
    assert custom_formatter.cdata_containing_tags == custom_tags


@given(st.sampled_from([Formatter.HTML, Formatter.XML, "invalid", None]))
def test_language_setting(language):
    """Test that language is set correctly in formatter."""
    if language in [Formatter.HTML, Formatter.XML, "invalid", None]:
        formatter = Formatter(language=language)
        if language is None:
            # Should default to HTML
            assert formatter.language == Formatter.HTML
        else:
            assert formatter.language == language


@given(st.text(min_size=0, max_size=10))
def test_void_element_close_prefix(prefix):
    """Test that void_element_close_prefix is stored correctly."""
    formatter = Formatter(void_element_close_prefix=prefix)
    assert formatter.void_element_close_prefix == prefix