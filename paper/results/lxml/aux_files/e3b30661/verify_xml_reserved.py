#!/usr/bin/env python3
"""Verify if 'xml' prefix is truly reserved in XML spec and if this is a bug"""

from lxml.builder import ElementMaker, E
from lxml import etree as ET

print("Verifying XML reserved name handling\n")

# According to W3C XML spec:
# "Names beginning with the string 'xml', or with any string which would match 
# (('X'|'x') ('M'|'m') ('L'|'l')), are reserved for standardization"

print("Test 1: Creating elements with 'xml' prefix using ElementMaker")
xml_tags = ['xml', 'XML', 'Xml', 'xMl', 'xmlversion', 'xmlnamespace']

for tag in xml_tags:
    elem = E(tag)
    serialized = ET.tostring(elem, encoding='unicode')
    print(f"  E('{tag}'): {serialized}")
print()

print("Test 2: Creating same elements with direct etree.Element")
for tag in xml_tags:
    elem = ET.Element(tag)
    serialized = ET.tostring(elem, encoding='unicode')
    print(f"  ET.Element('{tag}'): {serialized}")
print()

print("Test 3: Parsing XML with 'xml' prefixed tags")
for tag in xml_tags:
    xml_string = f"<{tag}/>"
    try:
        parsed = ET.fromstring(xml_string)
        print(f"  Parsing '<{tag}/>': Success")
    except ET.XMLSyntaxError as e:
        print(f"  Parsing '<{tag}/>': Failed - {e}")
print()

print("Test 4: Testing actual reserved XML attributes")
# These are actually reserved and have special meaning
elem = E('root')
elem.set('{http://www.w3.org/XML/1998/namespace}lang', 'en')  # xml:lang
elem.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')  # xml:space

serialized = ET.tostring(elem, encoding='unicode')
print(f"Element with xml:lang and xml:space: {serialized}")
print()

print("Test 5: Check if this is actually problematic")
# The XML spec says these names are reserved for future standardization
# but doesn't explicitly forbid their use as element names

# Try to create a document with these tags and validate
doc_string = b"""<?xml version="1.0" encoding="UTF-8"?>
<root>
    <xml>This is questionable</xml>
    <xmldata>Some data</xmldata>
    <normalTag>Normal content</normalTag>
</root>"""

try:
    doc = ET.fromstring(doc_string)
    print("Document with 'xml' prefixed tags parses successfully")
    
    # Check if we can round-trip
    serialized = ET.tostring(doc, encoding='unicode')
    reparsed = ET.fromstring(serialized)
    print("Round-trip successful")
except Exception as e:
    print(f"Error: {e}")
print()

print("Conclusion:")
print("- lxml (and the underlying libxml2) accepts element names starting with 'xml'")
print("- The XML spec says these are 'reserved for standardization'")
print("- This is more of a 'should not use' rather than 'must not use'")
print("- Not enforcing this could lead to future compatibility issues")
print("- This might be considered a minor spec compliance issue rather than a bug")