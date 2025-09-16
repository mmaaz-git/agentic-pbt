import pytest
from hypothesis import given, strategies as st, assume, settings
from bs4.formatter import Formatter, HTMLFormatter, XMLFormatter
from bs4.element import Tag
from bs4.dammit import EntitySubstitution
import re

# Strategy for generating attribute names - valid HTML/XML attribute names
attr_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_",
    min_size=1,
    max_size=20
).filter(lambda x: x[0].isalpha())  # Attribute names must start with a letter

# Strategy for attribute values
attr_value = st.text(min_size=0, max_size=100)

# Test 1: Attribute sorting property
@given(
    attrs=st.dictionaries(attr_name, attr_value, min_size=0, max_size=10)
)
def test_formatter_attributes_are_sorted(attrs):
    """Test that Formatter.attributes() always returns attributes sorted alphabetically by key."""
    formatter = Formatter()
    tag = Tag(name="test")
    tag.attrs = attrs
    
    result = list(formatter.attributes(tag))
    
    # Extract keys from result
    keys = [k for k, v in result]
    
    # Property: keys should be sorted
    assert keys == sorted(keys), f"Keys not sorted: {keys} != {sorted(keys)}"
    
    # Property: all original keys should be present
    assert set(keys) == set(attrs.keys()), f"Keys mismatch: {set(keys)} != {set(attrs.keys())}"


# Test 2: Empty attributes are booleans property
@given(
    attrs=st.dictionaries(
        attr_name,
        st.one_of(
            st.just(""),  # Empty string
            st.just(None),  # None value
            st.text(min_size=1, max_size=50)  # Non-empty string
        ),
        min_size=0,
        max_size=10
    )
)
def test_empty_attributes_are_booleans_conversion(attrs):
    """Test that empty string values are converted to None when empty_attributes_are_booleans=True."""
    formatter_with_bool = Formatter(empty_attributes_are_booleans=True)
    formatter_without_bool = Formatter(empty_attributes_are_booleans=False)
    
    tag = Tag(name="test")
    tag.attrs = attrs.copy()
    
    result_with_bool = dict(formatter_with_bool.attributes(tag))
    result_without_bool = dict(formatter_without_bool.attributes(tag))
    
    for key, value in attrs.items():
        if value == "":
            # When empty_attributes_are_booleans=True, empty strings should become None
            assert result_with_bool[key] is None, f"Empty string not converted to None for key {key}"
            # When empty_attributes_are_booleans=False, empty strings should stay as empty strings
            assert result_without_bool[key] == "", f"Empty string modified when it shouldn't be for key {key}"
        elif value is None:
            # None values should always stay as None
            assert result_with_bool[key] is None, f"None value changed for key {key}"
            assert result_without_bool[key] is None, f"None value changed for key {key}"
        else:
            # Non-empty strings should remain unchanged
            assert result_with_bool[key] == value, f"Non-empty value changed for key {key}"
            assert result_without_bool[key] == value, f"Non-empty value changed for key {key}"


# Test 3: Indent property - indentation should be consistent
@given(
    indent=st.one_of(
        st.integers(min_value=-5, max_value=10),
        st.text(alphabet=" \t", min_size=0, max_size=5),
        st.just(None)
    )
)
def test_formatter_indent_property(indent):
    """Test that the indent parameter is handled consistently."""
    formatter = Formatter(indent=indent)
    
    # According to the code:
    # - None should become 0 spaces
    # - Negative integers should become 0 spaces
    # - Positive integers should become that many spaces
    # - Strings should be used as-is
    # - Invalid types should default to single space
    
    if indent is None:
        assert formatter.indent == "", "None indent should result in empty string"
    elif isinstance(indent, int):
        if indent < 0:
            assert formatter.indent == "", f"Negative indent {indent} should result in empty string"
        else:
            assert formatter.indent == " " * indent, f"Integer indent {indent} should result in {indent} spaces"
    elif isinstance(indent, str):
        assert formatter.indent == indent, f"String indent should be preserved as-is"
    else:
        assert formatter.indent == " ", f"Invalid indent type should default to single space"


# Test 4: substitute_xml round-trip property
@given(
    text=st.text(min_size=0, max_size=100)
)
def test_xml_substitution_preserves_essential_characters(text):
    """Test that XML substitution preserves the essential structure while escaping special characters."""
    result = EntitySubstitution.substitute_xml(text)
    
    # Property: The only changes should be escaping <, >, and &
    # Count occurrences of special characters in original
    lt_count = text.count('<')
    gt_count = text.count('>')
    amp_count = text.count('&')
    
    # These should be replaced in the result
    result_lt_count = result.count('&lt;')
    result_gt_count = result.count('&gt;')
    # For ampersands, we need to be careful as they might already be part of entities
    # Let's check that no unescaped < or > remain
    
    # Property: No unescaped < or > should remain
    # We need to check for < and > that aren't part of &lt; or &gt;
    remaining_lt = result.replace('&lt;', '').count('<')
    remaining_gt = result.replace('&gt;', '').count('>')
    
    assert remaining_lt == 0, f"Unescaped < found in result: {result}"
    assert remaining_gt == 0, f"Unescaped > found in result: {result}"


# Test 5: HTML5 vs HTML entity substitution differences
@given(
    text=st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=0, 
        max_size=50
    )
)
def test_html5_less_aggressive_than_html(text):
    """Test that html5 substitution is less or equally aggressive about escaping ampersands than html."""
    html_result = EntitySubstitution.substitute_html(text)
    html5_result = EntitySubstitution.substitute_html5(text)
    
    # Property: HTML5 should never escape MORE ampersands than HTML
    # Count escaped ampersands
    html_escaped_amp_count = html_result.count('&amp;')
    html5_escaped_amp_count = html5_result.count('&amp;')
    
    assert html5_escaped_amp_count <= html_escaped_amp_count, \
        f"HTML5 escaped more ampersands ({html5_escaped_amp_count}) than HTML ({html_escaped_amp_count}) for text: {text}"


# Test 6: Formatter language defaults
@given(
    language=st.sampled_from([Formatter.HTML, Formatter.XML, None])
)
def test_formatter_language_affects_defaults(language):
    """Test that the language setting properly affects default values."""
    formatter = Formatter(language=language)
    
    actual_language = language if language is not None else Formatter.HTML
    assert formatter.language == actual_language, f"Language not set correctly"
    
    # For XML, cdata_containing_tags should be empty
    # For HTML, it should contain script and style
    if actual_language == Formatter.XML:
        assert formatter.cdata_containing_tags == set(), \
            f"XML should have empty cdata_containing_tags, got {formatter.cdata_containing_tags}"
    else:  # HTML
        assert formatter.cdata_containing_tags == set(["script", "style"]), \
            f"HTML should have script and style in cdata_containing_tags, got {formatter.cdata_containing_tags}"


# Test 7: Attribute value substitution
@given(
    value=st.text(min_size=0, max_size=100)
)
def test_attribute_value_substitution(value):
    """Test that attribute_value method correctly applies substitution."""
    # Test with substitution function
    formatter_with_sub = Formatter(entity_substitution=EntitySubstitution.substitute_xml)
    # Test without substitution function
    formatter_without_sub = Formatter(entity_substitution=None)
    
    result_with_sub = formatter_with_sub.attribute_value(value)
    result_without_sub = formatter_without_sub.attribute_value(value)
    
    # Without substitution, value should be unchanged
    assert result_without_sub == value, f"Value changed when no substitution: {value} -> {result_without_sub}"
    
    # With substitution, special characters should be escaped
    if '<' in value or '>' in value or '&' in value:
        # Result should be different if special characters are present
        if '<' in value:
            assert '&lt;' in result_with_sub or '<' not in result_with_sub.replace('&lt;', '')
        if '>' in value:
            assert '&gt;' in result_with_sub or '>' not in result_with_sub.replace('&gt;', '')


# Test 8: Test substitute round-trip with mixed content
@given(
    parts=st.lists(
        st.one_of(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=10),
            st.sampled_from(["<", ">", "&", "&amp;", "&lt;", "&gt;"])
        ),
        min_size=0,
        max_size=10
    )
)
def test_substitute_xml_containing_entities_preserves_entities(parts):
    """Test that substitute_xml_containing_entities preserves existing entities."""
    text = "".join(parts)
    
    # Use substitute_xml_containing_entities which should preserve existing entities
    result = EntitySubstitution.substitute_xml_containing_entities(text)
    
    # Property: Existing &lt; &gt; &amp; should be preserved
    # New < > & should be escaped
    
    # Count entities in original
    original_lt_entity = text.count('&lt;')
    original_gt_entity = text.count('&gt;')
    original_amp_entity = text.count('&amp;')
    
    # These should still be present in result
    result_lt_entity = result.count('&lt;')
    result_gt_entity = result.count('&gt;')
    
    # The result should have at least as many entity references as the original
    assert result_lt_entity >= original_lt_entity, \
        f"Lost &lt; entities: had {original_lt_entity}, now {result_lt_entity}"
    assert result_gt_entity >= original_gt_entity, \
        f"Lost &gt; entities: had {original_gt_entity}, now {result_gt_entity}"


if __name__ == "__main__":
    # Run a quick check of all tests
    print("Running property-based tests for bs4.formatter...")
    test_formatter_attributes_are_sorted()
    test_empty_attributes_are_booleans_conversion()
    test_formatter_indent_property()
    test_xml_substitution_preserves_essential_characters()
    test_html5_less_aggressive_than_html()
    test_formatter_language_affects_defaults()
    test_attribute_value_substitution()
    test_substitute_xml_containing_entities_preserves_entities()
    print("Quick check passed! Run with pytest for full testing.")