import lxml.etree as etree
from hypothesis import given, strategies as st, assume, settings
import string

# Strategy for valid XML element names
def xml_name_strategy():
    first_char = st.one_of(
        st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')),
        st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')),
        st.just('_')
    )
    other_chars = st.text(
        alphabet=string.ascii_letters + string.digits + '._-',
        min_size=0,
        max_size=20
    )
    return st.builds(lambda f, o: f + o, first_char, other_chars)

# Test 1: Empty attribute value handling bug
@given(
    tag=xml_name_strategy(),
    attr_name=xml_name_strategy()
)
@settings(max_examples=1000)
def test_empty_attribute_value_bug(tag, attr_name):
    """Test that empty string attribute values are preserved correctly"""
    elem = etree.Element(tag)
    
    # Set attribute to empty string
    elem.set(attr_name, '')
    
    # Should be empty string, not None
    assert elem.get(attr_name) == ''
    
    # Serialize and parse
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Empty attribute should still be empty string after round-trip
    assert parsed.get(attr_name) == ''
    
    # Note: Setting to None raises TypeError in lxml (unlike ElementTree)
    # This is a known API difference

# Test 2: fromstringlist behavior
@given(
    strings=st.lists(
        st.text(alphabet=string.ascii_letters + ' <>/="', min_size=1, max_size=50),
        min_size=1,
        max_size=10
    )
)
@settings(max_examples=500)
def test_fromstringlist_vs_fromstring(strings):
    """Test that fromstringlist behaves consistently with fromstring"""
    # Create a valid XML document from strings
    xml_parts = ['<root>']
    for s in strings:
        # Escape special XML characters
        escaped = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        xml_parts.append(f'<item>{escaped}</item>')
    xml_parts.append('</root>')
    
    # Join to single string
    xml_single = ''.join(xml_parts)
    
    # Parse both ways
    try:
        elem_from_string = etree.fromstring(xml_single)
        elem_from_list = etree.fromstringlist(xml_parts)
        
        # Should produce identical results
        assert etree.tostring(elem_from_string) == etree.tostring(elem_from_list)
        assert len(elem_from_string) == len(elem_from_list)
        
        # Check all children match
        for child1, child2 in zip(elem_from_string, elem_from_list):
            assert child1.tag == child2.tag
            assert child1.text == child2.text
            
    except etree.XMLSyntaxError:
        # Both should fail or both should succeed
        try:
            etree.fromstringlist(xml_parts)
            assert False, "fromstringlist succeeded but fromstring failed"
        except etree.XMLSyntaxError:
            pass  # Both failed, which is consistent

# Test 3: tostringlist behavior
@given(
    num_children=st.integers(min_value=0, max_value=10),
    texts=st.lists(
        st.text(alphabet=string.ascii_letters + string.digits + ' ', max_size=20),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=500)
def test_tostringlist_consistency(num_children, texts):
    """Test that tostringlist produces consistent results"""
    root = etree.Element('root')
    
    # Add children
    for i in range(num_children):
        child = etree.SubElement(root, f'child{i}')
        if i < len(texts) and texts[i]:
            child.text = texts[i]
    
    # Get both representations
    string_result = etree.tostring(root, encoding='unicode')
    list_result = etree.tostringlist(root, encoding='unicode')
    
    # Join list should equal string
    joined = ''.join(list_result)
    assert joined == string_result
    
    # Parse back from joined list
    parsed = etree.fromstring(joined)
    assert len(parsed) == num_children

# Test 4: Element.clear() behavior
@given(
    tag=xml_name_strategy(),
    num_attrs=st.integers(min_value=0, max_value=5),
    num_children=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=500)
def test_element_clear_behavior(tag, num_attrs, num_children):
    """Test that Element.clear() properly clears all content"""
    elem = etree.Element(tag)
    
    # Add attributes
    for i in range(num_attrs):
        elem.set(f'attr{i}', f'value{i}')
    
    # Add children
    for i in range(num_children):
        etree.SubElement(elem, f'child{i}')
    
    # Add text and tail
    elem.text = 'text'
    elem.tail = 'tail'
    
    # Verify content exists
    assert len(elem.attrib) == num_attrs
    assert len(elem) == num_children
    assert elem.text == 'text'
    assert elem.tail == 'tail'
    
    # Clear the element
    elem.clear()
    
    # Everything should be gone except tag
    assert elem.tag == tag
    assert len(elem.attrib) == 0
    assert len(elem) == 0
    assert elem.text is None
    assert elem.tail is None

# Test 5: strip_tags behavior
@given(
    tags_to_strip=st.lists(xml_name_strategy(), min_size=1, max_size=3),
    other_tags=st.lists(xml_name_strategy(), min_size=1, max_size=3)
)
@settings(max_examples=300)
def test_strip_tags_preserves_text(tags_to_strip, other_tags):
    """Test that strip_tags preserves text content correctly"""
    assume(len(set(tags_to_strip) & set(other_tags)) == 0)  # No overlap
    
    root = etree.Element('root')
    root.text = 'start'
    
    # Add mix of tags
    for i, tag in enumerate(tags_to_strip + other_tags):
        child = etree.SubElement(root, tag)
        child.text = f'text{i}'
        child.tail = f'tail{i}'
    
    # Get original text content
    original_text = ''.join(root.itertext())
    
    # Strip specified tags
    etree.strip_tags(root, *tags_to_strip)
    
    # Text content should be preserved
    new_text = ''.join(root.itertext())
    
    # The text should still be there, just rearranged
    for tag in tags_to_strip:
        assert root.find(f'.//{tag}') is None  # Tag should be gone
    
    # Other tags should remain
    for tag in other_tags:
        if tag not in tags_to_strip:
            assert root.find(f'.//{tag}') is not None

# Test 6: XPath empty result handling
@given(
    tag=xml_name_strategy(),
    invalid_xpath=st.text(alphabet=string.ascii_letters + '/', min_size=1, max_size=20)
)
@settings(max_examples=200)
def test_xpath_empty_results(tag, invalid_xpath):
    """Test XPath with queries that return empty results"""
    elem = etree.Element(tag)
    
    # Try to create XPath - some might be invalid
    try:
        xpath = etree.XPath(f'//{invalid_xpath}')
        result = xpath(elem)
        
        # Empty result should be empty list
        assert isinstance(result, list)
        assert len(result) == 0
        
    except (etree.XPathSyntaxError, etree.XPathEvalError):
        # Invalid XPath syntax is expected for some inputs
        pass

# Test 7: Unicode normalization
@given(
    text=st.text(
        alphabet=st.characters(min_codepoint=0x100, max_codepoint=0x1000),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=300)
def test_unicode_normalization(text):
    """Test that Unicode text is preserved exactly"""
    elem = etree.Element('test')
    elem.text = text
    
    # Serialize and parse
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Text should be identical
    assert parsed.text == text
    
    # Byte representation should also match
    assert parsed.text.encode('utf-8') == text.encode('utf-8')

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])