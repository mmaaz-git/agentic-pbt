from hypothesis import given, strategies as st, settings
import lxml.objectify as obj
from lxml import etree
import pytest


@given(st.text(min_size=0, max_size=10))
@settings(max_examples=500)
def test_xml_special_chars_in_values(text):
    """Test that XML special characters in values are handled correctly"""
    # Skip if text contains control characters that are invalid in XML
    if any(ord(c) < 32 and c not in '\t\n\r' for c in text):
        return
    
    xml_str = f'<root><value>{text}</value></root>'
    
    try:
        parsed = obj.fromstring(xml_str)
        
        # Serialize and reparse
        serialized = etree.tostring(parsed, encoding='unicode')
        reparsed = obj.fromstring(serialized)
        
        # Values should be equal after round-trip
        assert str(parsed.value) == str(reparsed.value)
    except etree.XMLSyntaxError:
        # This is expected for invalid XML characters
        pass


@given(st.sampled_from(['<', '>', '&', '"', "'"]))
def test_xml_entity_characters(char):
    """Test XML entity characters are escaped properly"""
    xml_str = f'<root><value>{char}</value></root>'
    
    try:
        parsed = obj.fromstring(xml_str)
        assert str(parsed.value) == char
        
        serialized = etree.tostring(parsed, encoding='unicode')
        reparsed = obj.fromstring(serialized)
        
        assert str(reparsed.value) == char
    except etree.XMLSyntaxError as e:
        # If it fails to parse, that's a bug - these should be auto-escaped
        print(f"Failed to parse XML with character '{char}': {e}")
        raise


@given(st.text(alphabet='<>&"\'', min_size=1, max_size=5))
def test_multiple_xml_entities(text):
    """Test combinations of XML entity characters"""
    xml_str = f'<root><value>{text}</value></root>'
    
    try:
        parsed = obj.fromstring(xml_str)
        serialized = etree.tostring(parsed, encoding='unicode')
        reparsed = obj.fromstring(serialized)
        assert str(reparsed.value) == text
    except etree.XMLSyntaxError:
        # These characters should be handled
        pytest.fail(f"Failed to handle XML entities in: {repr(text)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])