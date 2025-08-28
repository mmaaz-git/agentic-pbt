"""Test which character ranges fail in ElementInclude text includes."""

import os
import tempfile
from lxml import etree, ElementInclude

def test_all_control_characters():
    """Test all control characters from 0x00 to 0x1F."""
    
    failed_chars = []
    succeeded_chars = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test control characters 0x00 to 0x1F
        for i in range(0x20):  # 0x00 to 0x1F
            char = chr(i)
            
            # Create text file
            text_file = os.path.join(tmpdir, f"test_{i:02x}.txt")
            try:
                with open(text_file, 'wb') as f:
                    f.write(char.encode('utf-8'))
            except:
                continue  # Skip if char can't be encoded
            
            # Test text include
            xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{text_file}" parse="text"/>
</root>'''
            
            tree = etree.fromstring(xml_content.encode())
            
            try:
                ElementInclude.include(tree)
                succeeded_chars.append(i)
            except ValueError as e:
                if "XML compatible" in str(e):
                    failed_chars.append(i)
            except Exception:
                pass  # Other errors
    
    print("Control Character Test Results:")
    print("=" * 50)
    print(f"Failed characters (rejected by ElementInclude):")
    for i in failed_chars:
        name = {
            0x00: "NULL",
            0x01: "Start of Heading",
            0x02: "Start of Text",
            0x03: "End of Text",
            0x04: "End of Transmission",
            0x05: "Enquiry",
            0x06: "Acknowledge",
            0x07: "Bell",
            0x08: "Backspace",
            0x0B: "Vertical Tab",
            0x0C: "Form Feed",
            0x0E: "Shift Out",
            0x0F: "Shift In",
            0x10: "Data Link Escape",
            0x11: "Device Control 1",
            0x12: "Device Control 2",
            0x13: "Device Control 3",
            0x14: "Device Control 4",
            0x15: "Negative Acknowledge",
            0x16: "Synchronous Idle",
            0x17: "End of Transmission Block",
            0x18: "Cancel",
            0x19: "End of Medium",
            0x1A: "Substitute",
            0x1B: "Escape",
            0x1C: "File Separator",
            0x1D: "Group Separator",
            0x1E: "Record Separator",
            0x1F: "Unit Separator",
        }.get(i, f"Control-{i:02X}")
        print(f"  0x{i:02X}: {name}")
    
    print(f"\nSucceeded characters (accepted by ElementInclude):")
    for i in succeeded_chars:
        name = {
            0x09: "Tab",
            0x0A: "Line Feed",
            0x0D: "Carriage Return",
        }.get(i, f"Control-{i:02X}")
        print(f"  0x{i:02X}: {name}")
    
    return failed_chars, succeeded_chars


def demonstrate_bug_with_real_use_case():
    """Demonstrate a real-world scenario where this bug causes problems."""
    
    print("\n" + "=" * 50)
    print("Real-world Bug Scenario:")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a CSV-like file with field separators (common in data processing)
        data_file = os.path.join(tmpdir, "data.txt")
        
        # Using Unit Separator (0x1F) - a standard ASCII delimiter
        # This is commonly used in data formats
        data = "Field1\x1FField2\x1FField3"
        
        with open(data_file, 'wb') as f:
            f.write(data.encode('utf-8'))
        
        print(f"Created data file with Unit Separator (0x1F) as delimiter")
        print(f"File contents (repr): {repr(data)}")
        
        # Try to include this in XML documentation
        xml_content = f'''<?xml version="1.0"?>
<documentation xmlns:xi="http://www.w3.org/2001/XInclude">
    <description>Here is the data:</description>
    <data>
        <xi:include href="{data_file}" parse="text"/>
    </data>
</documentation>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        try:
            ElementInclude.include(tree)
            print("✓ Successfully included data file")
        except ValueError as e:
            print(f"✗ FAILED to include data file: {e}")
            print("\nThis is a bug because:")
            print("1. The Unit Separator (0x1F) is a valid ASCII/Unicode character")
            print("2. It's commonly used as a field delimiter in data processing")
            print("3. Text includes should preserve raw text content as-is")
            print("4. The XML spec allows these characters in CDATA sections")
            return False
    
    return True


if __name__ == "__main__":
    failed, succeeded = test_all_control_characters()
    
    if failed:
        print(f"\nBUG: {len(failed)} control characters are incorrectly rejected")
        print(f"Only {len(succeeded)} control characters are accepted")
    
    demonstrate_bug_with_real_use_case()