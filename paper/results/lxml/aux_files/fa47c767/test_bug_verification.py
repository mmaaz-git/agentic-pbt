"""Verify that the bug is in ElementInclude, not in the underlying etree."""

import os
import tempfile
from lxml import etree, ElementInclude

def test_etree_cdata_support():
    """Test if etree itself can handle control characters in CDATA."""
    
    print("Testing if lxml.etree can handle control characters in CDATA:")
    print("=" * 50)
    
    # Control character
    control_char = '\x1f'
    
    # Try creating element with control char in CDATA
    root = etree.Element("root")
    
    # Test 1: Can we put control chars in CDATA?
    try:
        # CDATA should allow any character except ]]>
        cdata_content = f"Data with control char: {control_char}"
        # Note: lxml doesn't have direct CDATA API, but we can work around it
        
        # This is what ElementInclude is trying to do:
        root.text = control_char
        print(f"✗ Setting text with control char succeeded (unexpected!)")
    except ValueError as e:
        print(f"✓ Setting text with control char failed: {e}")
        print("  This confirms lxml doesn't allow control chars in text nodes")
    
    # Test 2: What about using a different approach?
    print("\nAlternative approach - using CDATA explicitly:")
    try:
        # In theory, CDATA should work, but lxml may not expose this properly
        doc = etree.fromstring(f'<root><![CDATA[{control_char}]]></root>'.encode('utf-8'))
        print(f"✓ Parsing XML with CDATA containing control char succeeded")
        print(f"  Content: {repr(doc.text)}")
    except Exception as e:
        print(f"✗ Parsing failed: {e}")


def test_xml_spec_compliance():
    """Check what the XML spec says about text content."""
    
    print("\n" + "=" * 50)
    print("XML Specification Context:")
    print("=" * 50)
    
    print("According to XML 1.0 spec:")
    print("- Characters 0x00-0x08, 0x0B-0x0C, 0x0E-0x1F are NOT allowed in XML 1.0")
    print("- Only 0x09 (tab), 0x0A (LF), 0x0D (CR) are allowed from control chars")
    print("- These restrictions apply to text nodes, not CDATA sections")
    print()
    print("However, for XInclude with parse='text':")
    print("- The included content is NOT XML, it's plain text")
    print("- The spec says: 'Resources included as text are character information'")
    print("- Text includes should preserve the exact bytes/characters")
    print()
    print("BUG ANALYSIS:")
    print("ElementInclude is incorrectly treating text includes as XML text nodes")
    print("instead of preserving them as raw character data.")


def test_spec_compliant_behavior():
    """Test what SHOULD happen according to XInclude spec."""
    
    print("\n" + "=" * 50)
    print("Expected Behavior per XInclude Specification:")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a binary file with control characters
        binary_file = os.path.join(tmpdir, "binary.dat")
        
        # Common use case: Including a data file with delimiters
        # Using Record Separator (0x1E) and Unit Separator (0x1F)
        data = "Record1\x1FField1\x1FField2\x1ERecord2\x1FField1\x1FField2"
        
        with open(binary_file, 'wb') as f:
            f.write(data.encode('utf-8'))
        
        print("Test case: Including data with ASCII delimiters")
        print(f"Data contains Record Separator (0x1E) and Unit Separator (0x1F)")
        print(f"Data preview: {repr(data[:50])}")
        
        xml_content = f'''<?xml version="1.0"?>
<document xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{binary_file}" parse="text"/>
</document>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        print("\nWhat SHOULD happen (per XInclude spec):")
        print("✓ The text content should be included as-is")
        print("✓ Control characters should be preserved")
        print("✓ No XML validation should apply to text includes")
        
        print("\nWhat ACTUALLY happens:")
        try:
            ElementInclude.include(tree)
            print("✓ Include succeeded")
        except ValueError as e:
            print(f"✗ Include failed: {e}")
            print("\nThis violates the XInclude specification!")


if __name__ == "__main__":
    test_etree_cdata_support()
    test_xml_spec_compliance()
    test_spec_compliant_behavior()