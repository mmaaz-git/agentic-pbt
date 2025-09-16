import lxml.etree as etree

# Minimal reproduction of the CDATA carriage return bug
def test_cdata_carriage_return_bug():
    # Create a CDATA section with carriage return
    root = etree.Element("root")
    original_text = "\r"
    root.text = etree.CDATA(original_text)
    
    # Serialize to XML
    xml_string = etree.tostring(root, encoding='unicode')
    print(f"Serialized XML: {xml_string!r}")
    
    # Parse back
    parsed = etree.fromstring(xml_string)
    parsed_text = parsed.text
    
    print(f"Original text: {original_text!r}")
    print(f"Parsed text:   {parsed_text!r}")
    print(f"Are they equal? {parsed_text == original_text}")
    
    assert parsed_text == original_text, f"CDATA content changed: {original_text!r} -> {parsed_text!r}"

if __name__ == "__main__":
    test_cdata_carriage_return_bug()