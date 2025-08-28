#!/usr/bin/env python3
"""Test for namespace handling issues in lxml.builder"""

from lxml.builder import ElementMaker, E
from lxml import etree as ET

print("Testing namespace handling edge cases\n")

# Test 1: Same namespace prefix mapping to different URIs
print("Test 1: Namespace prefix collision")
E1 = ElementMaker(namespace='http://ns1.com/', nsmap={'ns': 'http://ns1.com/'})
E2 = ElementMaker(namespace='http://ns2.com/', nsmap={'ns': 'http://ns2.com/'})

elem1 = E1('parent')
elem2 = E2('child')
elem1.append(elem2)

serialized = ET.tostring(elem1, encoding='unicode')
print(f"Serialized: {serialized}")
parsed = ET.fromstring(serialized)
print(f"Parent namespace: {parsed.tag}")
print(f"Child namespace: {parsed[0].tag}")
print()

# Test 2: Empty namespace after non-empty
print("Test 2: Mixed empty and non-empty namespaces")
E1 = ElementMaker(namespace='http://example.com/')
E2 = ElementMaker()  # No namespace

parent = E1('parent')
child = E2('child')
parent.append(child)

serialized = ET.tostring(parent, encoding='unicode')
print(f"Serialized: {serialized}")
print()

# Test 3: Namespace inheritance
print("Test 3: Namespace inheritance test")
E_ns = ElementMaker(namespace='http://example.com/', nsmap={'ex': 'http://example.com/'})
parent = E_ns('parent')
# Add text and child without namespace
parent.text = 'text'
child = E('child')  # Using the default E without namespace
parent.append(child)

serialized = ET.tostring(parent, encoding='unicode')
print(f"Serialized: {serialized}")
parsed = ET.fromstring(serialized)
print(f"Child full tag: {parsed[0].tag}")
print()

# Test 4: Default namespace vs prefixed namespace
print("Test 4: Default namespace behavior")
E_default = ElementMaker(namespace='http://default.com/')
E_prefixed = ElementMaker(namespace='http://prefixed.com/', nsmap={'pre': 'http://prefixed.com/'})

elem_default = E_default('default')
elem_prefixed = E_prefixed('prefixed')

print(f"Default NS: {ET.tostring(elem_default, encoding='unicode')}")
print(f"Prefixed NS: {ET.tostring(elem_prefixed, encoding='unicode')}")
print()

# Test 5: Very long namespace URI
print("Test 5: Long namespace URI")
long_ns = 'http://example.com/' + 'a' * 1000
E_long = ElementMaker(namespace=long_ns)
elem = E_long('tag')
serialized = ET.tostring(elem, encoding='unicode')
print(f"Long namespace works, serialized length: {len(serialized)}")
print()

# Test 6: Special characters in namespace
print("Test 6: Special characters in namespace URI")
test_namespaces = [
    'http://example.com/path?query=1',
    'http://example.com/path#fragment',
    'http://example.com/path with spaces',  # This might be invalid
    'urn:example:namespace',
    'http://example.com/ünicode',
]

for ns in test_namespaces:
    try:
        E_test = ElementMaker(namespace=ns)
        elem = E_test('tag')
        serialized = ET.tostring(elem, encoding='unicode')
        print(f"  {ns[:30]}...: OK")
    except Exception as e:
        print(f"  {ns[:30]}...: Failed - {e}")
print()

# Test 7: Namespace map with None key
print("Test 7: None as namespace prefix")
try:
    E_none = ElementMaker(nsmap={None: 'http://default.com/'})
    elem = E_none('tag')
    serialized = ET.tostring(elem, encoding='unicode')
    print(f"None prefix result: {serialized}")
except Exception as e:
    print(f"None prefix failed: {e}")
print()

# Test 8: Multiple namespace maps
print("Test 8: Multiple namespace prefixes")
nsmap = {
    'ns1': 'http://ns1.com/',
    'ns2': 'http://ns2.com/',
    'ns3': 'http://ns3.com/'
}
E_multi = ElementMaker(namespace='http://main.com/', nsmap=nsmap)
elem = E_multi('tag')
serialized = ET.tostring(elem, encoding='unicode')
print(f"Multiple namespaces: {serialized}")
print()

print("All namespace tests completed!")