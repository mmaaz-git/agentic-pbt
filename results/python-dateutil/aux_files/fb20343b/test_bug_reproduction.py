from lxml import etree, pyclasslookup


class CustomElement(etree.ElementBase):
    instances_created = 0
    
    def __init__(self):
        super().__init__()
        CustomElement.instances_created += 1


class AlwaysCustomLookup(pyclasslookup.PythonElementClassLookup):
    def __init__(self):
        super().__init__()
        self.lookup_count = 0
    
    def lookup(self, doc, element):
        self.lookup_count += 1
        return CustomElement


def test_multiple_iteration_bug():
    xml = '<root><child1/><child2/></root>'
    
    lookup = AlwaysCustomLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    CustomElement.instances_created = 0
    
    result = etree.XML(xml, parser)
    
    # First iteration
    elements_1 = list(result.iter())
    lookups_after_first = lookup.lookup_count
    
    # Second iteration - should not trigger more lookups
    elements_2 = list(result.iter())
    lookups_after_second = lookup.lookup_count
    
    print(f"XML has 3 elements: root, child1, child2")
    print(f"Lookups after first iteration: {lookups_after_first}")
    print(f"Lookups after second iteration: {lookups_after_second}")
    print(f"CustomElement instances created: {CustomElement.instances_created}")
    
    # The bug: lookup is called again for the same elements
    assert lookups_after_first == 3  # root + child1 + child2
    assert lookups_after_second == 6  # Bug: calls lookup again!
    
    return lookups_after_first, lookups_after_second


if __name__ == "__main__":
    test_multiple_iteration_bug()