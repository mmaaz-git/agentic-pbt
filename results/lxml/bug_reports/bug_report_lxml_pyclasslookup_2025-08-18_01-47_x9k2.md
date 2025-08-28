# Bug Report: lxml.pyclasslookup Custom Element __init__ Not Called

**Target**: `lxml.pyclasslookup.PythonElementClassLookup`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Custom `__init__` methods in ElementBase subclasses are not called when elements are created through PythonElementClassLookup, preventing proper initialization of custom element classes.

## Property-Based Test

```python
from lxml import etree, pyclasslookup
from hypothesis import given, strategies as st
import string


def valid_tag_name():
    first_char = st.sampled_from(string.ascii_letters + '_')
    other_chars = st.text(alphabet=string.ascii_letters + string.digits + '-_.', min_size=0, max_size=10)
    return st.builds(lambda f, o: f + o, first_char, other_chars)


class InitializedElement(etree.ElementBase):
    init_count = 0
    
    def __init__(self):
        super().__init__()
        InitializedElement.init_count += 1
        self.initialized = True


class InitLookup(pyclasslookup.PythonElementClassLookup):
    def lookup(self, doc, element):
        return InitializedElement


@given(valid_tag_name())
def test_custom_init_called(tag):
    xml = f'<{tag}/>'
    InitializedElement.init_count = 0
    
    lookup = InitLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    result = etree.XML(xml, parser)
    
    assert isinstance(result, InitializedElement)
    assert hasattr(result, 'initialized')  # Fails - attribute not set
    assert InitializedElement.init_count > 0  # Fails - __init__ never called
```

**Failing input**: Any valid XML tag triggers the bug

## Reproducing the Bug

```python
from lxml import etree, pyclasslookup


class CustomElement(etree.ElementBase):
    def __init__(self):
        super().__init__()
        self.custom_data = "initialized"


class CustomLookup(pyclasslookup.PythonElementClassLookup):
    def lookup(self, doc, element):
        if element.tag == "custom":
            return CustomElement
        return None


xml = '<root><custom/></root>'
lookup = CustomLookup()
parser = etree.XMLParser()
parser.set_element_class_lookup(lookup)

result = etree.XML(xml, parser)
custom_elem = result[0]

print(f"Is CustomElement: {isinstance(custom_elem, CustomElement)}")  # True
print(f"Has custom_data: {hasattr(custom_elem, 'custom_data')}")  # False - Bug!
```

## Why This Is A Bug

The PythonElementClassLookup documentation and API contract implies that returning a custom ElementBase subclass will create instances of that class. Standard Python behavior expects that when an instance of a class is created, its `__init__` method is called. This bug violates that fundamental expectation, making it impossible to properly initialize custom element classes with instance-specific data or perform initialization logic.

This prevents common patterns like:
- Setting default attributes on custom elements
- Registering elements in tracking structures
- Initializing element-specific state
- Performing validation during element creation

## Fix

The fix would require modifying lxml's C implementation to properly call the Python `__init__` method after creating element instances through the lookup mechanism. Since this is in the C extension code, a high-level approach would be:

1. After instantiating the custom element class in the C code
2. Check if the class has a custom `__init__` method
3. Call the `__init__` method with appropriate arguments
4. Handle any exceptions that may occur during initialization

The issue likely stems from the fact that lxml creates element instances at the C level for performance reasons, bypassing the normal Python object creation protocol that would trigger `__init__`.