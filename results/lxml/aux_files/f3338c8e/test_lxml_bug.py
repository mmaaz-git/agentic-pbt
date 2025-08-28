import math
from hypothesis import given, strategies as st, settings
import lxml.objectify as obj
from lxml import etree
import pytest


@given(st.text(min_size=0, max_size=1).filter(lambda s: s in ['', ' ']))
def test_empty_value_bug(value):
    """Test that empty string values are preserved correctly"""
    xml_str = f'<root><value>{value}</value></root>'
    parsed = obj.fromstring(xml_str)
    
    if value == '':
        serialized = etree.tostring(parsed, encoding='unicode')
        reparsed = obj.fromstring(serialized)
        
        print(f"Original value: {repr(parsed.value)}, type: {type(parsed.value).__name__}")
        print(f"Reparsed value: {repr(reparsed.value)}, type: {type(reparsed.value).__name__}")
        
        assert str(parsed.value) == ''
        assert str(reparsed.value) == ''


@given(st.sampled_from(['', ' ', '\t', '\n']))
def test_whitespace_value_preservation(value):
    """Test whitespace value preservation through XML round-trip"""
    xml_str = f'<root><value>{value}</value></root>'
    parsed = obj.fromstring(xml_str)
    
    serialized = etree.tostring(parsed, encoding='unicode')
    reparsed = obj.fromstring(serialized)
    
    print(f"Input: {repr(value)}")
    print(f"Original: {repr(str(parsed.value))}, type: {type(parsed.value).__name__}")
    print(f"Reparsed: {repr(str(reparsed.value))}, type: {type(reparsed.value).__name__}")
    
    assert str(parsed.value) == str(reparsed.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])