# Bug Report: lxml.etree Element.set() API Inconsistency with None Values

**Target**: `lxml.etree.Element.set()`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

`lxml.etree.Element.set()` raises TypeError when passed None as a value, while `xml.etree.ElementTree.Element.set()` removes the attribute, causing API incompatibility between the two implementations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import lxml.etree as etree

def xml_name_strategy():
    first_char = st.one_of(
        st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')),
        st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')),
        st.just('_')
    )
    other_chars = st.text(
        alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-',
        min_size=0,
        max_size=20
    )
    return st.builds(lambda f, o: f + o, first_char, other_chars)

@given(tag=xml_name_strategy(), attr_name=xml_name_strategy())
def test_set_attribute_none_compatibility(tag, attr_name):
    elem = etree.Element(tag)
    elem.set(attr_name, 'value')
    
    # This should remove the attribute (like ElementTree does)
    elem.set(attr_name, None)
    assert elem.get(attr_name) is None
```

**Failing input**: Any valid tag and attribute name, e.g., `tag='_A', attr_name='_'`

## Reproducing the Bug

```python
import lxml.etree as etree
import xml.etree.ElementTree as ET

# Standard library behavior - removes the attribute
elem_et = ET.Element('test')
elem_et.set('attr', 'value')
elem_et.set('attr', None)
print(f"ElementTree after set(None): {elem_et.get('attr')}")  # None

# lxml behavior - raises TypeError
elem_lxml = etree.Element('test')
elem_lxml.set('attr', 'value')
try:
    elem_lxml.set('attr', None)
    print(f"lxml after set(None): {elem_lxml.get('attr')}")
except TypeError as e:
    print(f"lxml raises: {e}")  # Argument must be bytes or unicode, got 'NoneType'
```

## Why This Is A Bug

This violates the principle of least surprise and breaks code portability between `xml.etree.ElementTree` and `lxml.etree`. The standard library's ElementTree API treats `set(attr, None)` as a way to remove an attribute, which is intuitive and consistent with Python's general use of None to indicate absence. Code written for ElementTree will fail when switched to lxml, even though lxml is intended to be a drop-in replacement with extended functionality.

## Fix

The fix would involve modifying the `_setAttributeValue` function in lxml to handle None values specially:

```diff
--- a/src/lxml/apihelpers.pxi
+++ b/src/lxml/apihelpers.pxi
@@ -592,6 +592,10 @@ cdef int _setAttributeValue(
         attr_ns_utf, attr_name_utf = _getNsTag(attr_name)
         if attr_ns_utf is not None:
             c_ns = _xcstr(attr_ns_utf)
+    # Handle None value like ElementTree does - remove the attribute
+    if value is None:
+        _delAttribute(element, attr_name)
+        return 0
     value_utf = _utf8(value)
     if attr_ns_utf is not None:
         tree.xmlSetNsProp(element._c_node, c_ns, attr_name_utf, value_utf)
```

Alternatively, users must use `del elem.attrib[attr_name]` or `elem.attrib.pop(attr_name, None)` to remove attributes in lxml, but this breaks compatibility with code written for ElementTree.