from hypothesis import given, strategies as st, settings
import lxml.objectify as obj
from lxml import etree
import pytest


@given(st.sampled_from(['<', '&', '"', "'"]))
def test_element_maker_doesnt_escape_special_chars(char):
    """ElementMaker doesn't properly escape XML special characters"""
    E = obj.E
    
    # Create element with special character
    elem = E.root(E.value(char))
    
    # This should work but might fail if not escaped properly
    xml_str = etree.tostring(elem, encoding='unicode')
    
    # Parse it back
    reparsed = obj.fromstring(xml_str)
    
    # The value should be preserved
    assert str(reparsed.value) == char


@given(st.text(alphabet='<>&"\'', min_size=1, max_size=5))
def test_element_maker_with_multiple_special_chars(text):
    """ElementMaker should handle combinations of special chars"""
    E = obj.E
    
    # Create element with text containing special chars
    elem = E.root(E.data(text))
    
    # Serialize
    xml_str = etree.tostring(elem, encoding='unicode')
    
    # Parse back
    reparsed = obj.fromstring(xml_str)
    
    # Value should be preserved
    assert str(reparsed.data) == text


@given(st.text(min_size=1, max_size=50).filter(lambda s: any(c in s for c in '<>&"\'')))
def test_subelement_with_special_chars(text):
    """SubElement should handle special characters"""
    root = obj.Element('root')
    sub = obj.SubElement(root, 'value')
    sub._setText(text)
    
    # Serialize and reparse
    xml_str = etree.tostring(root, encoding='unicode')
    reparsed = obj.fromstring(xml_str)
    
    assert str(reparsed.value) == text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])