import lxml.etree as etree

def test_empty_value_bug():
    """Test potential bug with empty attribute values"""
    
    # Create element with empty attribute value
    elem = etree.Element("root")
    elem.set("attr", "")
    
    # Test different serialization methods
    xml_unicode = etree.tostring(elem, encoding='unicode')
    xml_utf8 = etree.tostring(elem, encoding='utf-8')
    
    print(f"Unicode: {xml_unicode}")
    print(f"UTF-8:   {xml_utf8}")
    
    # Parse back
    parsed_unicode = etree.fromstring(xml_unicode)
    parsed_utf8 = etree.fromstring(xml_utf8)
    
    print(f"\nParsed from unicode: attr={parsed_unicode.get('attr')!r}")
    print(f"Parsed from UTF-8:   attr={parsed_utf8.get('attr')!r}")
    
    # Test with None vs empty string
    elem2 = etree.Element("test")
    elem2.set("a", "")
    elem2.set("b", None)  # This should remove the attribute
    
    xml2 = etree.tostring(elem2, encoding='unicode')
    print(f"\nWith None: {xml2}")
    
    return True

if __name__ == "__main__":
    test_empty_value_bug()