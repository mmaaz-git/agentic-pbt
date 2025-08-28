# Bug Report: lxml.sax Empty String Text Accumulation

**Target**: `lxml.sax.ElementTreeContentHandler.characters`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `ElementTreeContentHandler.characters()` method incorrectly converts `None` text to an empty string when an empty string is added, violating XML serialization conventions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from lxml.sax import ElementTreeContentHandler

@given(texts=st.lists(st.text(min_size=0, max_size=10), min_size=1, max_size=10))
def test_multiple_text_accumulation(texts):
    handler = ElementTreeContentHandler()
    handler.startElementNS((None, "root"), "root", None)
    
    accumulated = ""
    for text in texts:
        handler.characters(text)
        accumulated += text
    
    handler.endElementNS((None, "root"), "root")
    result = handler.etree.getroot()
    
    expected = accumulated if accumulated else None
    assert result.text == expected
```

**Failing input**: `texts=['']`

## Reproducing the Bug

```python
from lxml import etree
from lxml.sax import ElementTreeContentHandler

handler = ElementTreeContentHandler()
handler.startElementNS((None, 'root'), 'root', None)
handler.characters('')
handler.endElementNS((None, 'root'), 'root')

result = handler.etree.getroot()

print(f"Result text: {result.text!r}")
print(f"Expected: None")
print(f"Bug confirmed: {result.text == ''}")

normal_element = etree.Element('root')
print(f"\nSerialization comparison:")
print(f"Normal element: {etree.tostring(normal_element, encoding='unicode')}")
print(f"SAX with empty: {etree.tostring(result, encoding='unicode')}")
```

## Why This Is A Bug

In lxml/ElementTree, element text should be `None` when there's no text content, which serializes as `<root/>`. An empty string `''` represents empty text content and serializes as `<root></root>`. The SAX handler incorrectly converts `None` to `''` when accumulating an empty string, changing the XML serialization behavior.

## Fix

```diff
--- a/lxml/sax.py
+++ b/lxml/sax.py
@@ -155,7 +155,10 @@ class ElementTreeContentHandler(ContentHandler):
             last_element.tail = (last_element.tail or '') + data
         except IndexError:
             # otherwise: append to the text
-            last_element.text = (last_element.text or '') + data
+            if data:
+                last_element.text = (last_element.text or '') + data
+            elif last_element.text is None:
+                last_element.text = None
 
     ignorableWhitespace = characters
```

A simpler fix would be:

```diff
--- a/lxml/sax.py
+++ b/lxml/sax.py
@@ -149,6 +149,8 @@ class ElementTreeContentHandler(ContentHandler):
 
     def characters(self, data):
+        if not data:
+            return
         last_element = self._element_stack[-1]
         try:
             # if there already is a child element, we must append to its tail
```