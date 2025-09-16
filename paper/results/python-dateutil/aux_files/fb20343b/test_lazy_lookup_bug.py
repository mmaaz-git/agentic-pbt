"""
Test demonstrating the lazy lookup behavior of PythonElementClassLookup.
This shows that lookup() is NOT called for all elements during parsing,
but only when elements are accessed.
"""

from lxml import etree, pyclasslookup
from hypothesis import given, strategies as st


class CountingLookup(pyclasslookup.PythonElementClassLookup):
    def __init__(self):
        super().__init__()
        self.lookup_count = 0
        self.elements_seen = []
    
    def lookup(self, doc, element):
        self.lookup_count += 1
        self.elements_seen.append(element.tag)
        return None


def demonstrate_lazy_lookup_issue():
    """
    Demonstrates that PythonElementClassLookup.lookup() is called lazily,
    not during initial parsing.
    """
    
    xml = '<root><child1><grandchild/></child1><child2/></root>'
    
    # First, count elements in the tree
    tree = etree.fromstring(xml)
    total_elements = len(list(tree.iter()))
    print(f"Total elements in XML: {total_elements}")
    print(f"Elements: {[e.tag for e in tree.iter()]}")
    
    # Now parse with custom lookup
    lookup = CountingLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    print("\n1. After parsing (etree.XML):")
    result = etree.XML(xml, parser)
    print(f"   Lookup count: {lookup.lookup_count}")
    print(f"   Elements seen: {lookup.elements_seen}")
    
    print("\n2. After accessing root.tag:")
    _ = result.tag
    print(f"   Lookup count: {lookup.lookup_count}")
    print(f"   Elements seen: {lookup.elements_seen}")
    
    print("\n3. After accessing first child (result[0]):")
    child1 = result[0]
    print(f"   Lookup count: {lookup.lookup_count}")
    print(f"   Elements seen: {lookup.elements_seen}")
    
    print("\n4. After iterating all elements:")
    all_tags = [e.tag for e in result.iter()]
    print(f"   Lookup count: {lookup.lookup_count}")
    print(f"   Elements seen: {lookup.elements_seen}")
    
    print("\n5. After iterating again:")
    all_tags_2 = [e.tag for e in result.iter()]
    print(f"   Lookup count: {lookup.lookup_count}")
    print(f"   Elements seen: {lookup.elements_seen}")
    
    # Check if lookup was called for each element at least once
    unique_elements_seen = set(lookup.elements_seen)
    expected_elements = set(e.tag for e in tree.iter())
    
    print(f"\nExpected to see: {expected_elements}")
    print(f"Actually saw: {unique_elements_seen}")
    print(f"Missing elements: {expected_elements - unique_elements_seen}")
    
    # The issue: lookup is called lazily and may not be called for all elements
    # unless they are explicitly accessed
    return lookup.lookup_count, total_elements


def test_fromstring_vs_parse_behavior():
    """Test if fromstring behaves differently from parse"""
    xml = '<root><child/></root>'
    
    print("\nTesting etree.fromstring with custom parser:")
    lookup1 = CountingLookup()
    parser1 = etree.XMLParser()
    parser1.set_element_class_lookup(lookup1)
    
    # Note: fromstring doesn't accept parser argument
    # result1 = etree.fromstring(xml, parser1)  # This doesn't work
    
    print("\nTesting etree.XML with custom parser:")
    lookup2 = CountingLookup()
    parser2 = etree.XMLParser()
    parser2.set_element_class_lookup(lookup2)
    
    result2 = etree.XML(xml, parser2)
    print(f"After etree.XML: {lookup2.lookup_count} lookups")
    _ = list(result2.iter())
    print(f"After iteration: {lookup2.lookup_count} lookups")


if __name__ == "__main__":
    print("=" * 60)
    print("Demonstrating lazy lookup behavior")
    print("=" * 60)
    
    demonstrate_lazy_lookup_issue()
    
    print("\n" + "=" * 60)
    test_fromstring_vs_parse_behavior()