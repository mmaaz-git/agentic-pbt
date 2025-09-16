#!/usr/bin/env python3
"""Specific targeted tests for potential bugs in lxml.builder"""

from lxml.builder import ElementMaker, E
from lxml import etree as ET

print("Testing potential bug scenarios in lxml.builder\n")

# Test 1: Empty value handling
print("Test 1: Empty attribute name")
try:
    elem = E('tag', {'': 'value'})  # This should fail
    print("Result: Should have failed but didn't!")
except ValueError as e:
    print(f"Result: Correctly failed with: {e}")
print()

# Test 2: Attribute value escaping
print("Test 2: Attribute value with quotes")
elem = E('tag', {'attr': 'value"with"quotes'})
serialized = ET.tostring(elem, encoding='unicode')
print(f"Serialized: {serialized}")
parsed = ET.fromstring(serialized)
print(f"Round-trip value: {parsed.attrib['attr']}")
assert parsed.attrib['attr'] == 'value"with"quotes'
print()

# Test 3: Multiple text nodes behavior
print("Test 3: Multiple consecutive text nodes")
elem = E('tag', 'text1', 'text2', 'text3')
serialized = ET.tostring(elem, encoding='unicode')
print(f"Serialized: {serialized}")
parsed = ET.fromstring(serialized)
assert parsed.text == 'text1text2text3'
print()

# Test 4: Mixed content with empty strings
print("Test 4: Mixed content with empty strings")
elem = E('root', '', E('child'), '')
serialized = ET.tostring(elem, encoding='unicode')
print(f"Serialized: {serialized}")
# Check if empty strings affect the structure
print()

# Test 5: Nested ElementMaker instances
print("Test 5: Using different ElementMaker instances")
E1 = ElementMaker(namespace='http://ns1.com/')
E2 = ElementMaker(namespace='http://ns2.com/')
elem1 = E1('tag1')
elem2 = E2('tag2')
elem1.append(elem2)
serialized = ET.tostring(elem1, encoding='unicode')
print(f"Mixed namespaces: {serialized}")
print()

# Test 6: Attribute order preservation (non-guaranteed in XML but interesting)
print("Test 6: Attribute ordering")
attrs = {'z': '1', 'a': '2', 'm': '3'}
elem = E('tag', attrs)
serialized = ET.tostring(elem, encoding='unicode')
print(f"Attributes: {serialized}")
parsed = ET.fromstring(serialized)
print(f"Parsed attrs: {parsed.attrib}")
print()

# Test 7: Special method names as tags
print("Test 7: Python special method names as tags")
special_names = ['__init__', '__call__', '__str__', '__repr__']
for name in special_names:
    try:
        elem = E(name)
        print(f"  {name}: OK - {ET.tostring(elem, encoding='unicode')}")
    except Exception as e:
        print(f"  {name}: Failed - {e}")
print()

# Test 8: Unicode tag names (valid in XML but might have issues)
print("Test 8: Unicode tag names")
unicode_tags = ['café', 'привет', '你好', '🦄']  
for tag in unicode_tags:
    try:
        elem = E(tag)
        print(f"  {tag}: OK - {ET.tostring(elem, encoding='unicode')}")
    except Exception as e:
        print(f"  {tag}: Failed - {e}")
print()

# Test 9: Very deeply nested tail text
print("Test 9: Deeply nested tail text")
root = E('root')
current = root
for i in range(10):
    child = E(f'level{i}')
    current.append(child)
    child.tail = f'tail{i}'
    current = child

serialized = ET.tostring(root, encoding='unicode')
parsed = ET.fromstring(serialized)

# Check tails are preserved
current = parsed
for i in range(10):
    child = current[0]
    assert child.tail == f'tail{i}'
    current = child
print("All tail texts preserved correctly")
print()

# Test 10: Entity references in text
print("Test 10: Entity references")
test_texts = [
    '&amp;',
    '&lt;',
    '&gt;',
    '&quot;',
    '&apos;',
    '&#65;',  # Numeric entity for 'A'
    '&#x41;',  # Hex entity for 'A'
]

for text in test_texts:
    elem = E('tag', text)
    serialized = ET.tostring(elem, encoding='unicode')
    print(f"  Input: {text:10} -> Serialized: {serialized}")
    parsed = ET.fromstring(serialized)
    print(f"    Round-trip: {parsed.text}")
print()

# Test 11: Invalid but commonly attempted patterns
print("Test 11: Common misuse patterns")

# Trying to pass non-string as tag
try:
    elem = E(123)
    print("  Numeric tag: Should have failed")
except TypeError as e:
    print(f"  Numeric tag: Correctly rejected - {e}")

# Trying to pass list as content
try:
    elem = E('tag', ['item1', 'item2'])
    print("  List content: Should have failed")
except TypeError as e:
    print(f"  List content: Correctly rejected - {e}")

print("\nAll tests completed!")