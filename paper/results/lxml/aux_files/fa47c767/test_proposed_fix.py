"""Test a proposed fix for the control character bug."""

import os
import tempfile
from lxml import etree

def escape_control_chars(text):
    """Escape control characters for XML text nodes using character references."""
    result = []
    for char in text:
        code = ord(char)
        # Control chars that are not allowed in XML 1.0
        if code < 0x20 and code not in (0x09, 0x0A, 0x0D):
            # Use numeric character reference
            result.append(f'&#{code};')
        else:
            result.append(char)
    return ''.join(result)


def fixed_text_include(tree, text_content, parent, predecessor, e):
    """Fixed version of text include logic that properly handles control chars."""
    
    # The current broken code does this:
    # parent.text = (parent.text or "") + text + (e.tail or "")
    
    # Fixed approach: escape control characters as numeric references
    escaped_text = escape_control_chars(text_content)
    
    if predecessor is not None:
        predecessor.tail = (predecessor.tail or "") + escaped_text
    else:
        parent.text = (parent.text or "") + escaped_text + (e.tail or "")
    
    parent.remove(e)


def test_fix():
    """Test if the fix works."""
    
    print("Testing proposed fix for control character handling:")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create text file with control chars
        text_file = os.path.join(tmpdir, "data.txt")
        test_data = "Field1\x1FField2\x1ERecord2"  # Unit and Record separators
        
        with open(text_file, 'wb') as f:
            f.write(test_data.encode('utf-8'))
        
        # Create XML
        xml = f'''<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <before>Before</before>
    <xi:include href="{text_file}" parse="text"/>
    <after>After</after>
</root>'''
        
        tree = etree.fromstring(xml.encode())
        
        # Find the include element
        xi_ns = "{http://www.w3.org/2001/XInclude}"
        include_elem = tree.find(f".//{xi_ns}include")
        
        print(f"Original text data: {repr(test_data)}")
        print(f"Escaped version: {repr(escape_control_chars(test_data))}")
        
        # Apply the fix
        parent = include_elem.getparent()
        predecessor = include_elem.getprevious()
        
        # Read the file content
        with open(text_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Apply fixed logic
        fixed_text_include(tree, text_content, parent, predecessor, include_elem)
        
        # Check result
        result_str = etree.tostring(tree, encoding='unicode')
        print(f"\nResult XML: {result_str}")
        
        # Verify the content is preserved (though escaped)
        if '&#31;' in result_str and '&#30;' in result_str:
            print("\n✓ Fix successful! Control characters preserved as numeric references")
            print("  This maintains XML validity while preserving the data")
        else:
            print("\n✗ Fix failed")


def demonstrate_escape_equivalence():
    """Show that escaped control chars are equivalent when parsed."""
    
    print("\n" + "=" * 50)
    print("Demonstrating escape equivalence:")
    print("=" * 50)
    
    # XML with escaped control char
    xml_escaped = '<root>Field1&#31;Field2</root>'
    tree = etree.fromstring(xml_escaped.encode())
    
    print(f"XML with escaped char: {xml_escaped}")
    print(f"Parsed text content: {repr(tree.text)}")
    print(f"Character at position 6: 0x{ord(tree.text[6]):02x}")
    
    if tree.text[6] == '\x1f':
        print("✓ Escaped character reference correctly produces control character")
    else:
        print("✗ Escape didn't work as expected")


if __name__ == "__main__":
    test_fix()
    demonstrate_escape_equivalence()