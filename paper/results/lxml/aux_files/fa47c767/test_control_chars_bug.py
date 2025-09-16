"""Investigate control character bug in lxml.ElementInclude"""

import os
import tempfile
from lxml import etree, ElementInclude

# Test case: Including text with control characters
def test_control_character_bug():
    """Demonstrate that ElementInclude fails on valid control characters in text files."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a text file with a control character (Unit Separator - ASCII 31)
        text_file = os.path.join(tmpdir, "text_with_control.txt")
        control_char = '\x1f'  # Unit Separator - a valid Unicode character
        
        with open(text_file, 'wb') as f:
            f.write(control_char.encode('utf-8'))
        
        # Create XML that includes this text file
        xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <before>Before</before>
    <xi:include href="{text_file}" parse="text" encoding="utf-8"/>
    <after>After</after>
</root>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        print("XML before include:")
        print(etree.tostring(tree, pretty_print=True).decode())
        
        try:
            # This should work - we're including valid UTF-8 text
            ElementInclude.include(tree)
            print("\nSuccessfully included text with control character")
            print("Result:", etree.tostring(tree, pretty_print=True).decode())
        except ValueError as e:
            print(f"\nFAILED: {e}")
            print("This is a bug! The text file contains valid UTF-8 data.")
            print("Control characters are valid in text files and should be includable.")
            return False
        
        return True


def test_control_character_xml_vs_text():
    """Compare how control characters are handled in XML vs text includes."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test various control characters
        control_chars = [
            ('\x00', 'NULL'),
            ('\x1f', 'Unit Separator'),
            ('\x09', 'Tab'),
            ('\x0a', 'Newline'),
            ('\x0d', 'Carriage Return'),
        ]
        
        for char, name in control_chars:
            print(f"\nTesting {name} (0x{ord(char):02x}):")
            
            # Create text file
            text_file = os.path.join(tmpdir, f"test_{ord(char)}.txt")
            with open(text_file, 'wb') as f:
                f.write(char.encode('utf-8'))
            
            # Test text include
            xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{text_file}" parse="text"/>
</root>'''
            
            tree = etree.fromstring(xml_content.encode())
            
            try:
                ElementInclude.include(tree)
                print(f"  ✓ Text include succeeded")
            except ValueError as e:
                print(f"  ✗ Text include failed: {e}")
            except Exception as e:
                print(f"  ✗ Text include failed (other): {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing control character handling in ElementInclude")
    print("=" * 60)
    
    if not test_control_character_bug():
        print("\nBUG CONFIRMED: ElementInclude incorrectly rejects valid text content")
    
    print("\n" + "=" * 60)
    print("Testing various control characters:")
    print("=" * 60)
    test_control_character_xml_vs_text()