#!/usr/bin/env python3
"""Investigation of control character handling in lxml.builder"""

from lxml.builder import ElementMaker, E
from lxml import etree as ET

# Test various control characters
control_chars = [
    ('\x00', 'NULL'),
    ('\x01', 'SOH'),
    ('\x02', 'STX'),
    ('\x03', 'ETX'),
    ('\x04', 'EOT'),
    ('\x05', 'ENQ'),
    ('\x06', 'ACK'),
    ('\x07', 'BEL'),
    ('\x08', 'BS'),
    ('\x09', 'TAB'),  # Valid in XML 1.0
    ('\x0A', 'LF'),   # Valid in XML 1.0
    ('\x0B', 'VT'),
    ('\x0C', 'FF'),
    ('\x0D', 'CR'),   # Valid in XML 1.0
    ('\x0E', 'SO'),
    ('\x0F', 'SI'),
    ('\x10', 'DLE'),
    ('\x1F', 'US'),
    ('\x7F', 'DEL'),
]

print("Testing control characters in text content:")
for char, name in control_chars:
    try:
        elem = E('tag', f'text{char}text')
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  {name} (\\x{ord(char):02x}): OK - {repr(serialized)}")
    except ValueError as e:
        print(f"  {name} (\\x{ord(char):02x}): REJECTED - {e}")

print("\nTesting control characters in attributes:")
for char, name in control_chars:
    try:
        elem = E('tag', {'attr': f'val{char}val'})
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  {name} (\\x{ord(char):02x}): OK - {repr(serialized)}")
    except ValueError as e:
        print(f"  {name} (\\x{ord(char):02x}): REJECTED - {e}")

# Now test if this is consistent with direct etree usage
print("\nDirect etree comparison (text):")
for char, name in control_chars:
    try:
        elem = ET.Element('tag')
        elem.text = f'text{char}text'
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  {name} (\\x{ord(char):02x}): OK - {repr(serialized)}")
    except ValueError as e:
        print(f"  {name} (\\x{ord(char):02x}): REJECTED - {e}")

print("\nDirect etree comparison (attributes):")
for char, name in control_chars:
    try:
        elem = ET.Element('tag', attr=f'val{char}val')
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  {name} (\\x{ord(char):02x}): OK - {repr(serialized)}")
    except ValueError as e:
        print(f"  {name} (\\x{ord(char):02x}): REJECTED - {e}")