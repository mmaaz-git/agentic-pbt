"""
Test that demonstrates custom __init__ is not called for ElementBase subclasses
"""

from lxml import etree, pyclasslookup
import sys


class CustomElement(etree.ElementBase):
    init_called_count = 0
    
    def __init__(self):
        # This should be called when element is created
        super().__init__()
        CustomElement.init_called_count += 1
        self.custom_attribute = "initialized"
        print(f"CustomElement.__init__ called! Count: {CustomElement.init_called_count}", file=sys.stderr)


class CustomLookup(pyclasslookup.PythonElementClassLookup):
    def lookup(self, doc, element):
        if element.tag == "custom":
            return CustomElement
        return None


def test_init_not_called():
    """
    Test that custom __init__ is not called when PythonElementClassLookup
    returns a custom element class.
    """
    
    xml = '<root><custom>text</custom><normal/></root>'
    
    # Reset counter
    CustomElement.init_called_count = 0
    
    # Set up parser with custom lookup
    lookup = CustomLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    # Parse XML
    print("Parsing XML with custom element class...")
    result = etree.XML(xml, parser)
    
    # Find custom elements
    custom_elements = [e for e in result.iter() if e.tag == "custom"]
    print(f"Found {len(custom_elements)} custom elements")
    
    # Check if they are CustomElement instances
    for elem in custom_elements:
        print(f"  Element tag: {elem.tag}")
        print(f"  Element type: {type(elem).__name__}")
        print(f"  Is CustomElement: {isinstance(elem, CustomElement)}")
        
        # Check if custom attribute exists
        if hasattr(elem, 'custom_attribute'):
            print(f"  Has custom_attribute: {elem.custom_attribute}")
        else:
            print(f"  Missing custom_attribute!")
    
    print(f"\nCustomElement.__init__ called {CustomElement.init_called_count} times")
    
    if CustomElement.init_called_count == 0:
        print("\nBUG: Custom __init__ was never called!")
        print("This means custom element initialization code is bypassed.")
        return True
    
    return False


def test_manual_creation():
    """Test that __init__ works when creating elements manually"""
    
    print("\nTesting manual element creation:")
    CustomElement.init_called_count = 0
    
    # This should call __init__
    elem = CustomElement()
    
    print(f"After manual creation:")
    print(f"  __init__ called: {CustomElement.init_called_count} times")
    print(f"  Has custom_attribute: {hasattr(elem, 'custom_attribute')}")
    
    if hasattr(elem, 'custom_attribute'):
        print(f"  custom_attribute value: {elem.custom_attribute}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing custom element __init__ behavior")
    print("=" * 60)
    
    bug_found = test_init_not_called()
    
    print("\n" + "=" * 60)
    test_manual_creation()
    
    if bug_found:
        print("\n" + "=" * 60)
        print("CRITICAL BUG CONFIRMED:")
        print("Custom __init__ methods are not called when elements are")
        print("created through PythonElementClassLookup!")
        print("This prevents proper initialization of custom element classes.")
        print("=" * 60)