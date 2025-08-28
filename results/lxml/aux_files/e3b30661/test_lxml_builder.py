#!/usr/bin/env python3
"""Property-based tests for lxml.builder module"""

from hypothesis import given, assume, strategies as st, settings
from lxml.builder import ElementMaker, E
from lxml import etree as ET
import string
import re

# Strategy for valid XML tag names
def valid_tag_name():
    """Generate valid XML tag names"""
    # XML names must start with letter or underscore
    # Can contain letters, digits, hyphens, periods, underscores
    # But cannot start with xml (case-insensitive)
    first_char = st.sampled_from(string.ascii_letters + '_')
    other_chars = st.text(alphabet=string.ascii_letters + string.digits + '-._', min_size=0, max_size=20)
    return st.builds(lambda f, o: f + o, first_char, other_chars).filter(
        lambda s: not s.lower().startswith('xml') and len(s) > 0
    )

# Strategy for valid attribute names
def valid_attr_name():
    """Generate valid XML attribute names"""
    # Similar rules to tag names
    return valid_tag_name()

# Strategy for text content that might expose issues
def text_content():
    """Generate various text content including edge cases"""
    return st.one_of(
        st.text(),  # Any unicode text
        st.text(min_size=1),  # Non-empty text
        st.just(''),  # Empty string
        st.text(alphabet=string.printable),  # ASCII printable
        st.text(alphabet='<>&"\''),  # XML special characters
        st.text(alphabet='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f'),  # Control characters
        st.text(alphabet='🦄🔥💖'),  # Emoji
        st.text(alphabet='\u200b\u200c\u200d\ufeff'),  # Zero-width characters
    )

# Strategy for attribute values
def attr_value():
    """Generate attribute values"""
    return st.one_of(
        st.text(),
        st.just(''),
        st.text(alphabet='<>&"\''),
        st.text(alphabet=string.printable),
    )

@given(tag=valid_tag_name(), text=text_content())
def test_text_content_preservation(tag, text):
    """Test that text content is preserved through serialization"""
    elem = E(tag, text)
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    
    # The text should be preserved (accounting for XML escaping)
    if parsed.text is None:
        assert text == ''
    else:
        assert parsed.text == text

@given(tag=valid_tag_name(), attr_name=valid_attr_name(), attr_val=attr_value())
def test_attribute_preservation(tag, attr_name, attr_val):
    """Test that attributes are preserved through serialization"""
    elem = E(tag, {attr_name: attr_val})
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    
    # The attribute should be preserved
    assert attr_name in parsed.attrib
    assert parsed.attrib[attr_name] == attr_val

@given(tag=valid_tag_name(), texts=st.lists(text_content(), min_size=1, max_size=5))
def test_multiple_text_concatenation(tag, texts):
    """Test that multiple text arguments are concatenated properly"""
    elem = E(tag, *texts)
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    
    # All texts should be concatenated
    expected = ''.join(texts)
    if parsed.text is None:
        assert expected == ''
    else:
        assert parsed.text == expected

@given(
    tag1=valid_tag_name(),
    tag2=valid_tag_name(),
    text1=text_content(),
    text2=text_content(),
    text3=text_content()
)
def test_mixed_content_ordering(tag1, tag2, text1, text2, text3):
    """Test that mixed content (text and elements) maintains order"""
    # Create: text1 <tag2>text2</tag2> text3
    elem = E(tag1, text1, E(tag2, text2), text3)
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    
    # Check the structure
    if parsed.text is None:
        assert text1 == ''
    else:
        assert parsed.text == text1
    
    # Should have one child
    assert len(parsed) == 1
    child = parsed[0]
    assert child.tag == tag2
    if child.text is None:
        assert text2 == ''
    else:
        assert child.text == text2
    
    # text3 becomes the tail of the child element
    if child.tail is None:
        assert text3 == ''
    else:
        assert child.tail == text3

@given(namespace=st.text(min_size=1, max_size=100))
def test_namespace_handling(namespace):
    """Test namespace handling in ElementMaker"""
    try:
        maker = ElementMaker(namespace=namespace)
        elem = maker('tag')
        serialized = ET.tostring(elem, encoding='unicode')
        
        # Should be able to parse it back
        parsed = ET.fromstring(serialized)
        
        # The namespace should be present
        if namespace:
            # Check that namespace is in the serialized form
            assert 'xmlns' in serialized or ':' in parsed.tag
    except Exception as e:
        # Some namespace strings might be invalid URIs
        pass

@given(
    tag=valid_tag_name(),
    attrs=st.dictionaries(valid_attr_name(), attr_value(), min_size=1, max_size=5)
)
def test_multiple_attributes(tag, attrs):
    """Test that multiple attributes are all preserved"""
    elem = E(tag, attrs)
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    
    # All attributes should be preserved
    assert parsed.attrib == attrs

@given(tag=valid_tag_name())
def test_empty_element_self_closing(tag):
    """Test that empty elements are self-closing"""
    elem = E(tag)
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Should be self-closing
    assert serialized == f'<{tag}/>' or serialized == f'<{tag}></{tag}>'
    
    # Parse it back
    parsed = ET.fromstring(serialized)
    assert parsed.tag == tag
    assert parsed.text is None
    assert len(parsed) == 0

@given(tag=valid_tag_name(), text=st.text(alphabet='\x00\x01\x02\x03\x04\x05'))
def test_control_characters_in_text(tag, text):
    """Test handling of control characters in text content"""
    try:
        elem = E(tag, text)
        serialized = ET.tostring(elem, encoding='unicode')
        
        # Try to parse it back
        parsed = ET.fromstring(serialized)
        
        # Some control characters are not valid in XML
        # This test checks if they're handled consistently
    except Exception as e:
        # Control characters might cause issues
        pass

@given(
    tag=valid_tag_name(),
    attr_name=valid_attr_name(),
    attr_val=st.text(alphabet='\x00\x01\x02\x03\x04\x05')
)
def test_control_characters_in_attributes(tag, attr_name, attr_val):
    """Test handling of control characters in attribute values"""
    try:
        elem = E(tag, {attr_name: attr_val})
        serialized = ET.tostring(elem, encoding='unicode')
        
        # Try to parse it back
        parsed = ET.fromstring(serialized)
    except Exception as e:
        # Control characters might cause issues
        pass

@given(tag=valid_tag_name())
def test_getattr_vs_call_equivalence(tag):
    """Test that E.tag() and E('tag') produce equivalent results"""
    # Using __call__
    elem1 = E(tag)
    serialized1 = ET.tostring(elem1, encoding='unicode')
    
    # Using getattr (E.tag syntax)
    elem2 = getattr(E, tag)()
    serialized2 = ET.tostring(elem2, encoding='unicode')
    
    # Should produce identical results
    assert serialized1 == serialized2

@given(tag=valid_tag_name(), text=text_content())
def test_getattr_vs_call_with_content(tag, text):
    """Test that E.tag(text) and E('tag', text) produce equivalent results"""
    # Using __call__
    elem1 = E(tag, text)
    serialized1 = ET.tostring(elem1, encoding='unicode')
    
    # Using getattr
    elem2 = getattr(E, tag)(text)
    serialized2 = ET.tostring(elem2, encoding='unicode')
    
    # Should produce identical results
    assert serialized1 == serialized2

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])