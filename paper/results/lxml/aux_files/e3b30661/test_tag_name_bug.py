#!/usr/bin/env python3
"""Test for XML tag name validation bug in lxml.builder"""

from lxml.builder import ElementMaker, E
from lxml import etree as ET
import string

print("Testing XML tag name validation\n")

# According to XML spec, names must:
# - Start with letter or underscore (or colon, but that's for namespaces)
# - Can contain letters, digits, hyphens, periods, underscores after first char
# - Cannot start with 'xml' (case-insensitive)

print("Test 1: Tags starting with digits (should fail per XML spec)")
digit_start_tags = ['0', '1tag', '123', '9abc', '0xff']
for tag in digit_start_tags:
    try:
        elem = E(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  '{tag}': ACCEPTED (potentially a bug?) - {serialized}")
        # Try to parse it back to see if it's valid XML
        try:
            parsed = ET.fromstring(serialized)
            print(f"    Parses back successfully!")
        except ET.XMLSyntaxError as e:
            print(f"    But fails to parse: {e}")
    except ValueError as e:
        print(f"  '{tag}': Correctly rejected - {e}")
print()

print("Test 2: Valid tag names that should work")
valid_tags = ['a', 'A', '_', 'abc123', 'tag-name', 'tag.name', 'tag_name', '_123']
for tag in valid_tags:
    try:
        elem = E(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        parsed = ET.fromstring(serialized)
        print(f"  '{tag}': OK")
    except Exception as e:
        print(f"  '{tag}': Unexpected error - {e}")
print()

print("Test 3: Tags with colons (namespace separator)")
colon_tags = ['ns:tag', ':tag', 'tag:', 'a:b:c']
for tag in colon_tags:
    try:
        elem = E(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  '{tag}': Accepted - {serialized}")
        try:
            parsed = ET.fromstring(serialized)
            print(f"    Parses back: {parsed.tag}")
        except ET.XMLSyntaxError as e:
            print(f"    But fails to parse: {e}")
    except ValueError as e:
        print(f"  '{tag}': Rejected - {e}")
print()

print("Test 4: Tags starting with 'xml' (should be reserved)")
xml_tags = ['xml', 'XML', 'Xml', 'xmltag', 'XMLTag', 'XmL']
for tag in xml_tags:
    try:
        elem = E(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  '{tag}': ACCEPTED (might be a bug for reserved prefix) - {serialized}")
        parsed = ET.fromstring(serialized)
    except ValueError as e:
        print(f"  '{tag}': Correctly rejected - {e}")
print()

print("Test 5: Special characters in tags")
special_tags = ['tag@name', 'tag#name', 'tag$name', 'tag%name', 'tag&name', 
                'tag*name', 'tag+name', 'tag=name', 'tag[name', 'tag]name',
                'tag{name', 'tag}name', 'tag|name', 'tag\\name', 'tag/name',
                'tag<name', 'tag>name', 'tag?name', 'tag!name', 'tag~name']
for tag in special_tags:
    try:
        elem = E(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  '{tag}': ACCEPTED (bug?) - {serialized}")
        try:
            parsed = ET.fromstring(serialized)
            print(f"    Parses back!")
        except:
            print(f"    But fails to parse")
    except ValueError as e:
        print(f"  '{tag}': Rejected")
print()

print("Test 6: Whitespace in tags")
space_tags = ['tag name', ' tag', 'tag ', 'tag\ttab', 'tag\nnewline']
for tag in space_tags:
    try:
        elem = E(tag)
        print(f"  '{repr(tag)}': ACCEPTED (definitely a bug!)")
    except ValueError as e:
        print(f"  '{repr(tag)}': Correctly rejected")
print()

print("Test 7: Empty and very short tags")
short_tags = ['', ' ', 'a', '_', '-', '.', ':', '1']
for tag in short_tags:
    try:
        elem = E(tag)
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  '{tag}': Accepted - {serialized}")
    except ValueError as e:
        print(f"  '{tag}': Rejected - {e}")
print()

print("\nSummary: Testing if lxml.builder properly validates XML tag names")
print("According to XML spec, tag names must start with letter or underscore")
print("but lxml.builder might not be enforcing this correctly.")