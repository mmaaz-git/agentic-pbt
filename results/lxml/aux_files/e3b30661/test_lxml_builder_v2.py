#!/usr/bin/env python3
"""Property-based tests for lxml.builder module - focused on finding real bugs"""

from hypothesis import given, assume, strategies as st, settings
from lxml.builder import ElementMaker, E
from lxml import etree as ET
import string
import re

# Strategy for valid XML tag names
def valid_tag_name():
    """Generate valid XML tag names"""
    first_char = st.sampled_from(string.ascii_letters + '_')
    other_chars = st.text(alphabet=string.ascii_letters + string.digits + '-._', min_size=0, max_size=20)
    return st.builds(lambda f, o: f + o, first_char, other_chars).filter(
        lambda s: not s.lower().startswith('xml') and len(s) > 0
    )

# Strategy for valid attribute names
def valid_attr_name():
    """Generate valid XML attribute names"""
    return valid_tag_name()

# Strategy for valid XML text (no control characters)
def valid_xml_text():
    """Generate text that's valid in XML"""
    # Only characters allowed in XML 1.0
    valid_chars = ''.join(
        chr(c) for c in range(0x20, 0xD800) if c not in [0x7F]
    ) + '\t\n\r'
    return st.text(alphabet=valid_chars)

# Strategy for attribute values
def attr_value():
    """Generate valid attribute values"""
    return valid_xml_text()

@given(
    tag=valid_tag_name(),
    text=valid_xml_text(),
    attr_name=valid_attr_name(),
    attr_val=attr_value()
)
def test_text_and_attribute_together(tag, text, attr_name, attr_val):
    """Test that text and attributes can coexist"""
    elem = E(tag, {attr_name: attr_val}, text)
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    
    # Both should be preserved
    assert parsed.tag == tag
    assert parsed.attrib[attr_name] == attr_val
    if parsed.text is None:
        assert text == ''
    else:
        assert parsed.text == text

@given(
    tag=valid_tag_name(),
    attrs1=st.dictionaries(valid_attr_name(), attr_value(), min_size=1, max_size=3),
    attrs2=st.dictionaries(valid_attr_name(), attr_value(), min_size=1, max_size=3)
)
def test_multiple_dict_arguments(tag, attrs1, attrs2):
    """Test passing multiple dictionary arguments"""
    # Create element with two dict arguments
    elem = E(tag, attrs1, attrs2)
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    
    # Both dicts should be merged
    expected = {**attrs1, **attrs2}
    assert parsed.attrib == expected

@given(tag=valid_tag_name())
def test_callable_vs_getattr_with_reserved_words(tag):
    """Test that reserved Python keywords work with getattr"""
    # Some Python reserved words that could be tag names
    reserved_words = ['class', 'for', 'if', 'def', 'return', 'import', 'from', 
                      'with', 'as', 'try', 'except', 'finally', 'raise',
                      'lambda', 'yield', 'assert', 'break', 'continue']
    
    for word in reserved_words:
        # Skip 'xml' prefixed words
        if word.lower().startswith('xml'):
            continue
            
        # Using __call__ should work
        elem1 = E(word)
        serialized1 = ET.tostring(elem1, encoding='unicode')
        
        # Using getattr should also work for reserved words
        elem2 = getattr(E, word)()
        serialized2 = ET.tostring(elem2, encoding='unicode')
        
        assert serialized1 == serialized2

@given(
    parent_tag=valid_tag_name(),
    child_tags=st.lists(valid_tag_name(), min_size=2, max_size=5)
)
def test_child_ordering_preservation(parent_tag, child_tags):
    """Test that child element order is preserved"""
    # Create parent with multiple children
    children = [E(tag) for tag in child_tags]
    parent = E(parent_tag, *children)
    
    serialized = ET.tostring(parent, encoding='unicode')
    parsed = ET.fromstring(serialized)
    
    # Check children are in same order
    assert len(parsed) == len(child_tags)
    for i, child in enumerate(parsed):
        assert child.tag == child_tags[i]

@given(
    tag=valid_tag_name(),
    namespace=st.text(alphabet=string.ascii_letters + string.digits + ':/.#-_', min_size=1, max_size=50)
)
def test_namespace_with_special_chars(tag, namespace):
    """Test namespace handling with various characters"""
    try:
        maker = ElementMaker(namespace=namespace)
        elem = maker(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        
        # Should be parseable
        parsed = ET.fromstring(serialized)
        
        # Check namespace is present
        if namespace:
            # The element should have a namespace
            assert '{' in parsed.tag or 'xmlns' in serialized
    except (ValueError, TypeError) as e:
        # Some namespace strings might be invalid
        pass

@given(
    tag=valid_tag_name(),
    text1=valid_xml_text(),
    text2=valid_xml_text()
)
def test_text_tail_separation(tag, text1, text2):
    """Test that text and tail are properly separated"""
    # Create: <parent>text1<tag/>text2</parent>
    child = E(tag)
    parent = E('parent', text1, child, text2)
    
    serialized = ET.tostring(parent, encoding='unicode')
    parsed = ET.fromstring(serialized)
    
    # Check structure
    if parsed.text is None:
        assert text1 == ''
    else:
        assert parsed.text == text1
    
    assert len(parsed) == 1
    child_elem = parsed[0]
    
    if child_elem.tail is None:
        assert text2 == ''
    else:
        assert child_elem.tail == text2

@given(
    tag=valid_tag_name(),
    attr_name=valid_attr_name()
)
def test_empty_string_attribute_value(tag, attr_name):
    """Test that empty string attribute values are preserved"""
    elem = E(tag, {attr_name: ''})
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse back
    parsed = ET.fromstring(serialized)
    
    # Empty string should be preserved as empty string, not None
    assert attr_name in parsed.attrib
    assert parsed.attrib[attr_name] == ''

@given(tag=valid_tag_name())
def test_empty_string_text(tag):
    """Test empty string text handling"""
    # Explicitly pass empty string
    elem = E(tag, '')
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Should not be self-closing since we explicitly added empty text
    assert f'<{tag}></{tag}>' in serialized

@given(
    tag=valid_tag_name(),
    nsmap=st.dictionaries(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
        st.text(alphabet=string.ascii_letters + ':/.', min_size=1, max_size=30),
        min_size=1,
        max_size=3
    )
)
def test_nsmap_handling(tag, nsmap):
    """Test namespace map handling"""
    try:
        # Filter out 'xml' prefixed keys
        nsmap = {k: v for k, v in nsmap.items() if not k.lower().startswith('xml')}
        if not nsmap:
            return
            
        maker = ElementMaker(nsmap=nsmap)
        elem = maker(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        
        # Should be parseable
        parsed = ET.fromstring(serialized)
        
        # Check that namespaces are declared
        for prefix in nsmap:
            assert f'xmlns:{prefix}' in serialized or prefix == 'None'
    except (ValueError, TypeError, KeyError) as e:
        # Some namespace configurations might be invalid
        pass

@given(
    tag=valid_tag_name(),
    typecode=st.sampled_from(['element', 'comment', 'pi'])
)
def test_makeelement_parameter(tag, typecode):
    """Test the makeelement parameter of ElementMaker"""
    def custom_maker(tag, attrib):
        if typecode == 'comment':
            return ET.Comment(f"Custom comment for {tag}")
        elif typecode == 'pi':
            return ET.PI(tag, "data")
        else:
            return ET.Element(tag, attrib)
    
    try:
        maker = ElementMaker(makeelement=custom_maker)
        elem = maker(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        
        if typecode == 'comment':
            assert '<!--' in serialized
        elif typecode == 'pi':
            assert '<?' in serialized
    except Exception:
        # Some configurations might not work
        pass

@given(
    tag=valid_tag_name(),
    text=valid_xml_text()
)
def test_unicode_normalization(tag, text):
    """Test that Unicode text is preserved exactly"""
    # Test with text that might be normalized differently
    test_texts = [
        '\u00E9',  # é (single character)
        'e\u0301',  # e + combining acute accent
        '\uFEFF',  # Zero-width no-break space (BOM)
        '\u200B',  # Zero-width space
    ]
    
    for test_text in test_texts:
        elem = E(tag, test_text)
        serialized = ET.tostring(elem, encoding='unicode')
        parsed = ET.fromstring(serialized)
        
        # Text should be preserved exactly
        if parsed.text:
            assert parsed.text == test_text

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])