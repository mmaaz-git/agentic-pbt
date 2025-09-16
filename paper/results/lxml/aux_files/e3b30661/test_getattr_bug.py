#!/usr/bin/env python3
"""Test for potential bugs in ElementMaker's __getattr__ functionality"""

from lxml.builder import ElementMaker, E
from lxml import etree as ET

print("Testing ElementMaker __getattr__ edge cases\n")

# Test 1: Reserved Python keywords
print("Test 1: Python reserved keywords as tag names")
keywords = ['class', 'for', 'if', 'def', 'return', 'import', 'from', 
            'with', 'as', 'try', 'except', 'finally', 'raise',
            'lambda', 'yield', 'assert', 'break', 'continue', 'pass',
            'global', 'nonlocal', 'del', 'is', 'in', 'not', 'and', 'or']

for kw in keywords:
    # Direct call should work
    elem1 = E(kw)
    s1 = ET.tostring(elem1, encoding='unicode')
    
    # getattr should also work
    elem2 = getattr(E, kw)()
    s2 = ET.tostring(elem2, encoding='unicode')
    
    if s1 != s2:
        print(f"  MISMATCH for '{kw}': {s1} != {s2}")
    else:
        print(f"  '{kw}': OK")
print()

# Test 2: Tags that look like ElementMaker methods
print("Test 2: Tags matching ElementMaker methods")
# ElementMaker has __init__, __call__, __getattr__
internal_names = ['__init__', '__call__', '__getattr__', '__class__', '__dict__']

for name in internal_names:
    try:
        # Direct call
        elem1 = E(name)
        s1 = ET.tostring(elem1, encoding='unicode')
        
        # Via getattr - this might return the actual method!
        attr = getattr(E, name)
        if callable(attr) and not isinstance(attr, ElementMaker):
            print(f"  '{name}': getattr returned actual method: {type(attr)}")
        else:
            elem2 = attr() if callable(attr) else attr
            s2 = ET.tostring(elem2, encoding='unicode')
            print(f"  '{name}': {s1 == s2}")
    except Exception as e:
        print(f"  '{name}': Error - {e}")
print()

# Test 3: Numeric-looking tags
print("Test 3: Numeric-looking tag names")
numeric_tags = ['123abc', 'abc123', '1.2.3', '0xff']

for tag in numeric_tags:
    try:
        # These start with numbers, so they're invalid XML
        elem = E(tag)
        print(f"  '{tag}': Should have failed but didn't!")
    except ValueError as e:
        print(f"  '{tag}': Correctly rejected - {e}")
print()

# Test 4: Tags with special characters
print("Test 4: Tags with special characters via getattr")
# Can't use getattr with these directly in Python
special_tags = ['tag-name', 'tag.name', 'tag:name']

for tag in special_tags:
    # Direct call might work
    try:
        elem1 = E(tag)
        s1 = ET.tostring(elem1, encoding='unicode')
        print(f"  '{tag}' direct: OK - {s1}")
    except Exception as e:
        print(f"  '{tag}' direct: Failed - {e}")
    
    # getattr won't work with these due to Python syntax
    try:
        elem2 = getattr(E, tag)()
        s2 = ET.tostring(elem2, encoding='unicode')
        print(f"  '{tag}' getattr: OK - {s2}")
    except AttributeError:
        print(f"  '{tag}' getattr: Expected AttributeError for invalid Python name")
    except Exception as e:
        print(f"  '{tag}' getattr: Unexpected error - {e}")
print()

# Test 5: Case sensitivity
print("Test 5: Case sensitivity")
tags = ['Tag', 'TAG', 'tag', 'TaG']
results = []
for tag in tags:
    elem = E(tag)
    results.append(ET.tostring(elem, encoding='unicode'))

print(f"  Results: {results}")
if len(set(results)) == len(results):
    print("  Case is preserved correctly")
else:
    print("  ISSUE: Case handling problem!")
print()

# Test 6: Very long tag names
print("Test 6: Very long tag names")
long_tag = 'a' * 1000
elem1 = E(long_tag)
elem2 = getattr(E, long_tag)()
s1 = ET.tostring(elem1, encoding='unicode')
s2 = ET.tostring(elem2, encoding='unicode')
print(f"  1000-char tag: {s1 == s2}")
print()

# Test 7: Empty string behavior
print("Test 7: Empty string as tag")
try:
    elem = E('')
    print("  Empty string: Should have failed!")
except ValueError as e:
    print(f"  Empty string: Correctly rejected - {e}")
print()

# Test 8: Unicode method names
print("Test 8: Unicode tag names via getattr")
unicode_tags = ['café', 'привет', '你好']

for tag in unicode_tags:
    # Direct call
    elem1 = E(tag)
    s1 = ET.tostring(elem1, encoding='unicode')
    
    # getattr with unicode
    try:
        elem2 = getattr(E, tag)()
        s2 = ET.tostring(elem2, encoding='unicode')
        if s1 == s2:
            print(f"  '{tag}': OK")
        else:
            print(f"  '{tag}': MISMATCH")
    except AttributeError:
        print(f"  '{tag}': getattr doesn't support unicode")
print()

print("All getattr tests completed!")