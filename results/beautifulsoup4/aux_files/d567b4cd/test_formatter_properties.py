import pytest
from hypothesis import given, strategies as st, assume
from bs4.element import Tag
from bs4.formatter import Formatter, HTMLFormatter, XMLFormatter
from bs4 import BeautifulSoup
import string

# Strategy for generating valid HTML attribute names
attr_name = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=1,
    max_size=20
).filter(lambda s: s[0].isalpha())

# Strategy for attribute values
attr_value = st.text(min_size=0, max_size=100)

# Strategy for generating dictionaries of attributes
attrs_dict = st.dictionaries(attr_name, attr_value, min_size=0, max_size=10)


@given(attrs_dict)
def test_attributes_always_sorted(attrs):
    """Test that Formatter.attributes() always returns sorted attributes."""
    formatter = Formatter()
    tag = Tag(name="test")
    
    # Set attributes
    for k, v in attrs.items():
        tag[k] = v
    
    # Get attributes from formatter
    result = list(formatter.attributes(tag))
    
    # Check they are sorted by key
    if result:
        keys = [k for k, v in result]
        assert keys == sorted(keys), f"Keys not sorted: {keys}"


@given(attrs_dict, st.booleans())
def test_empty_attributes_boolean_conversion(attrs, empty_attrs_bool):
    """Test that empty string values become None when empty_attributes_are_booleans is True."""
    formatter = Formatter(empty_attributes_are_booleans=empty_attrs_bool)
    tag = Tag(name="test")
    
    # Set attributes
    for k, v in attrs.items():
        tag[k] = v
    
    # Get attributes from formatter
    result = list(formatter.attributes(tag))
    
    for key, value in result:
        if empty_attrs_bool and attrs.get(key) == "":
            # Empty strings should be converted to None
            assert value is None, f"Empty string not converted to None for key {key}"
        else:
            # Other values should remain unchanged
            assert value == attrs.get(key), f"Value changed unexpectedly for key {key}"


@given(st.one_of(
    st.integers(min_value=-100, max_value=100),
    st.text(min_size=0, max_size=10),
    st.none()
))
def test_indent_normalization(indent_value):
    """Test that indent values are normalized correctly."""
    formatter = Formatter(indent=indent_value)
    
    if indent_value is None or (isinstance(indent_value, int) and indent_value <= 0):
        # Should become empty string
        assert formatter.indent == ""
    elif isinstance(indent_value, int):
        # Should become that many spaces
        assert formatter.indent == " " * indent_value
    elif isinstance(indent_value, str):
        # Should be used as-is
        assert formatter.indent == indent_value
    else:
        # Invalid types should default to single space
        assert formatter.indent == " "


@given(st.text(min_size=0, max_size=100))
def test_cdata_content_preservation(content):
    """Test that content in CDATA-containing tags is not entity-substituted."""
    from bs4.dammit import EntitySubstitution
    
    # Test with HTML formatter that has entity substitution
    formatter = HTMLFormatter(entity_substitution=EntitySubstitution.substitute_html)
    
    # Create a NavigableString-like object with a parent that is a CDATA tag
    from bs4.element import NavigableString
    
    # Test script tag (CDATA)
    script_tag = Tag(name="script")
    script_content = NavigableString(content)
    script_content.parent = script_tag
    
    # Content in script tag should not be substituted
    result = formatter.substitute(script_content)
    assert result == content, "Script tag content was substituted"
    
    # Test style tag (CDATA)
    style_tag = Tag(name="style")
    style_content = NavigableString(content)
    style_content.parent = style_tag
    
    # Content in style tag should not be substituted
    result = formatter.substitute(style_content)
    assert result == content, "Style tag content was substituted"
    
    # Test non-CDATA tag
    p_tag = Tag(name="p")
    p_content = NavigableString(content)
    p_content.parent = p_tag
    
    # Content in p tag should be substituted
    result = formatter.substitute(p_content)
    expected = EntitySubstitution.substitute_html(content)
    assert result == expected, "P tag content was not substituted correctly"


@given(st.sampled_from(['cdata_containing_tags']), st.sampled_from([Formatter.HTML, Formatter.XML]))
def test_language_defaults(kwarg, language):
    """Test that _default returns correct defaults based on language."""
    formatter = Formatter()
    
    # When value is None
    result = formatter._default(language, None, kwarg)
    
    if language == Formatter.XML:
        # XML should return empty set
        assert result == set(), f"XML didn't return empty set for {kwarg}"
    else:  # HTML
        # HTML should return the default from HTML_DEFAULTS
        expected = Formatter.HTML_DEFAULTS[kwarg]
        assert result == expected, f"HTML didn't return correct default for {kwarg}"
    
    # When value is provided, it should be returned as-is
    custom_value = {"custom", "tags"}
    result = formatter._default(language, custom_value, kwarg)
    assert result == custom_value, "Custom value not returned"


@given(st.sampled_from([None, "", 0, -1, -100]))
def test_indent_edge_cases(indent_value):
    """Test that various 'zero' indent values all normalize to empty string."""
    formatter = Formatter(indent=indent_value)
    assert formatter.indent == ""


@given(st.dictionaries(attr_name, attr_value, min_size=2, max_size=5))
def test_attributes_sorting_stability(attrs):
    """Test that attribute sorting is stable and consistent."""
    formatter = Formatter()
    tag = Tag(name="test")
    
    # Set attributes
    for k, v in attrs.items():
        tag[k] = v
    
    # Get attributes multiple times
    result1 = list(formatter.attributes(tag))
    result2 = list(formatter.attributes(tag))
    result3 = list(formatter.attributes(tag))
    
    # Should always return the same sorted order
    assert result1 == result2 == result3, "Attribute sorting is not stable"
    
    # Verify sorted by checking each adjacent pair
    for i in range(len(result1) - 1):
        assert result1[i][0] <= result1[i+1][0], f"Not properly sorted at index {i}"


@given(st.integers(min_value=0, max_value=50))
def test_indent_integer_to_spaces(spaces):
    """Test that integer indent values create the correct number of spaces."""
    formatter = Formatter(indent=spaces)
    assert formatter.indent == " " * spaces
    assert len(formatter.indent) == spaces