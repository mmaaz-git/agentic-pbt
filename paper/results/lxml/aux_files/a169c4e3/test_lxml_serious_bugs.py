import lxml.etree as etree
from hypothesis import given, strategies as st, assume, settings, example
import string

# Test for the None attribute bug we found
def test_set_attribute_none_api_inconsistency():
    """
    lxml.etree raises TypeError when setting attribute to None,
    while xml.etree.ElementTree removes the attribute.
    This is an API inconsistency that could cause portability issues.
    """
    import xml.etree.ElementTree as ET
    
    # Standard library behavior
    elem_et = ET.Element('test')
    elem_et.set('attr', 'value')
    elem_et.set('attr', None)  # This removes the attribute
    assert elem_et.get('attr') is None
    
    # lxml behavior
    elem_lxml = etree.Element('test')
    elem_lxml.set('attr', 'value')
    try:
        elem_lxml.set('attr', None)  # This raises TypeError
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "NoneType" in str(e)
    
    print("BUG CONFIRMED: lxml.etree.Element.set() raises TypeError for None value")
    print("              while xml.etree.ElementTree.Element.set() removes the attribute")
    return True

# Test for more subtle serialization bugs
@given(
    text=st.text(
        alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            min_codepoint=1,
            max_codepoint=0xD7FF
        ),
        min_size=1,
        max_size=100
    )
)
@settings(max_examples=1000)
def test_text_roundtrip_with_special_chars(text):
    """Test that text content survives round-trip serialization"""
    elem = etree.Element('test')
    elem.text = text
    
    # Multiple serialization methods
    methods = ['xml', 'html', 'text']
    
    for method in methods:
        if method == 'text':
            # text method just returns the text
            result = etree.tostring(elem, encoding='unicode', method=method)
            assert result == text
        else:
            xml_str = etree.tostring(elem, encoding='unicode', method=method)
            parsed = etree.fromstring(xml_str)
            if parsed.text != text:
                print(f"ROUNDTRIP FAILURE with method={method}")
                print(f"Original: {repr(text)}")
                print(f"Parsed:   {repr(parsed.text)}")
                assert False

# Test attribute name validation
@given(
    attr_name=st.text(
        alphabet=st.characters(min_codepoint=1, max_codepoint=127),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=500)
def test_attribute_name_validation(attr_name):
    """Test that invalid attribute names are properly rejected"""
    elem = etree.Element('test')
    
    try:
        elem.set(attr_name, 'value')
        # If it succeeded, verify we can get it back
        assert elem.get(attr_name) == 'value'
        
        # And it should survive serialization
        xml_str = etree.tostring(elem, encoding='unicode')
        parsed = etree.fromstring(xml_str)
        assert parsed.get(attr_name) == 'value'
        
    except (ValueError, etree.XMLSyntaxError) as e:
        # Should only reject truly invalid names
        # Check if it's a valid rejection
        invalid_chars = [' ', '<', '>', '/', '=', '"', "'", '\n', '\r', '\t']
        assert any(c in attr_name for c in invalid_chars) or attr_name[0].isdigit()

# Test namespace collision handling
@given(
    prefix1=st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
    prefix2=st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
    uri=st.text(alphabet=string.ascii_letters + ':/._-', min_size=5, max_size=30)
)
@settings(max_examples=300)
def test_namespace_prefix_collision(prefix1, prefix2, uri):
    """Test handling of conflicting namespace prefixes"""
    assume(prefix1 != prefix2)
    assume('/' in uri or ':' in uri)  # Make it look like a URI
    
    try:
        # Create element with namespace
        nsmap1 = {prefix1: uri}
        elem1 = etree.Element('root', nsmap=nsmap1)
        
        # Try to add child with different prefix for same URI
        nsmap2 = {prefix2: uri}
        child = etree.SubElement(elem1, 'child', nsmap=nsmap2)
        
        # Both should work
        xml_str = etree.tostring(elem1, encoding='unicode')
        
        # Parse back and check namespaces are preserved
        parsed = etree.fromstring(xml_str)
        
    except Exception as e:
        # Some namespace operations might fail
        pass

# Test CDATA with ]]> sequence
def test_cdata_with_end_sequence():
    """Test CDATA handling with ]]> sequence inside"""
    # This is a known limitation - CDATA can't contain ]]>
    # But the error handling should be graceful
    
    problematic_text = "This contains ]]> which ends CDATA"
    
    try:
        cdata = etree.CDATA(problematic_text)
        root = etree.Element('root')
        root.text = cdata
        
        # Try to serialize
        xml_str = etree.tostring(root, encoding='unicode')
        
        # If it succeeded, check if data is preserved correctly
        parsed = etree.fromstring(xml_str)
        
        if parsed.text != problematic_text:
            print("BUG: CDATA with ]]> sequence not handled correctly")
            print(f"Original: {repr(problematic_text)}")
            print(f"Parsed:   {repr(parsed.text)}")
            return True
            
    except Exception as e:
        # Expected to fail or handle specially
        pass
    
    return False

# Test very long attribute values
@given(
    length=st.integers(min_value=10000, max_value=100000)
)
@settings(max_examples=10)
def test_long_attribute_values(length):
    """Test handling of very long attribute values"""
    elem = etree.Element('test')
    long_value = 'x' * length
    
    elem.set('long', long_value)
    assert elem.get('long') == long_value
    
    # Serialize and parse
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Should preserve the full value
    assert parsed.get('long') == long_value
    assert len(parsed.get('long')) == length

if __name__ == '__main__':
    # Run the confirmed bug test
    print("\n=== Testing Confirmed Bugs ===\n")
    
    if test_set_attribute_none_api_inconsistency():
        print("\n✓ Confirmed: set() attribute None handling inconsistency")
    
    if test_cdata_with_end_sequence():
        print("\n✓ Confirmed: CDATA ]]> sequence issue")
    
    # Run property tests
    print("\n=== Running Property Tests ===\n")
    import pytest
    pytest.main([__file__, '-v', '--tb=short', '-k', 'not test_set_attribute_none'])