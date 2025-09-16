"""
Property-based test to identify potential caching issue in PythonElementClassLookup
"""

from lxml import etree, pyclasslookup
from hypothesis import given, strategies as st, settings
import string


# Strategy for valid XML tag names
def valid_tag_name():
    first_char = st.sampled_from(string.ascii_letters + '_')
    other_chars = st.text(alphabet=string.ascii_letters + string.digits + '-_.', min_size=0, max_size=10)
    return st.builds(lambda f, o: f + o, first_char, other_chars)


# Simple XML generation
@st.composite 
def simple_xml(draw):
    root_tag = draw(valid_tag_name())
    num_children = draw(st.integers(min_value=1, max_value=5))
    children = []
    for _ in range(num_children):
        child_tag = draw(valid_tag_name())
        children.append(f'<{child_tag}/>')
    return f'<{root_tag}>{"".join(children)}</{root_tag}>'


class StatefulLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that tracks state and can detect duplicate calls"""
    def __init__(self):
        super().__init__()
        self.lookup_count = 0
        self.element_lookup_counts = {}
    
    def lookup(self, doc, element):
        self.lookup_count += 1
        
        # Create a key for this element (tag + position in parent)
        key = element.tag
        parent = None
        try:
            # This might fail for root or proxy limitations
            parent = element.getparent()
        except:
            pass
        
        if parent is not None:
            # Find position in parent
            try:
                pos = list(parent).index(element)
                key = f"{element.tag}[parent={parent.tag},pos={pos}]"
            except:
                pass
        
        if key not in self.element_lookup_counts:
            self.element_lookup_counts[key] = 0
        self.element_lookup_counts[key] += 1
        
        return None


@given(simple_xml())
@settings(max_examples=100)
def test_lookup_caching_property(xml_str):
    """
    Property: Each unique element should have lookup called at most once per iteration.
    Multiple iterations should ideally use cached results.
    """
    
    try:
        # Parse normally to count elements
        tree = etree.fromstring(xml_str)
        total_elements = len(list(tree.iter()))
        
        # Parse with tracking lookup
        lookup = StatefulLookup()
        parser = etree.XMLParser()
        parser.set_element_class_lookup(lookup)
        
        result = etree.XML(xml_str, parser)
        
        # First full iteration
        tags1 = [e.tag for e in result.iter()]
        lookups_after_first = lookup.lookup_count
        
        # Second full iteration  
        tags2 = [e.tag for e in result.iter()]
        lookups_after_second = lookup.lookup_count
        
        # Third iteration
        tags3 = [e.tag for e in result.iter()]
        lookups_after_third = lookup.lookup_count
        
        # Check for excessive lookups
        # After first iteration, we expect one lookup per element
        assert lookups_after_first <= total_elements, \
            f"First iteration triggered {lookups_after_first} lookups for {total_elements} elements"
        
        # Subsequent iterations should ideally not trigger more lookups (caching)
        # But lxml doesn't cache - it calls lookup again for non-root elements
        additional_lookups_second = lookups_after_second - lookups_after_first
        additional_lookups_third = lookups_after_third - lookups_after_second
        
        # Check if lookups are consistent across iterations
        if additional_lookups_second > 0:
            # If there are additional lookups, they should be consistent
            # This reveals the bug: non-root elements get lookup called again
            non_root_elements = total_elements - 1
            
            # Bug: Each iteration after the first calls lookup again for non-root elements
            assert additional_lookups_second == non_root_elements, \
                f"Second iteration added {additional_lookups_second} lookups, expected {non_root_elements} for non-root elements"
            
            assert additional_lookups_third == non_root_elements, \
                f"Third iteration added {additional_lookups_third} lookups, expected {non_root_elements} for non-root elements"
        
        # Check for elements with excessive lookup counts
        for element_key, count in lookup.element_lookup_counts.items():
            if count > 3:  # After 3 iterations, no element should have more than 3 lookups
                print(f"Warning: Element {element_key} had lookup called {count} times")
        
    except etree.XMLSyntaxError:
        pass


def demonstrate_caching_issue():
    """Demonstrate the lack of caching in PythonElementClassLookup"""
    
    xml = '<root><a/><b/><c/></root>'
    
    lookup = StatefulLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    result = etree.XML(xml, parser)
    
    print("Testing multiple iterations:")
    for i in range(5):
        tags = [e.tag for e in result.iter()]
        print(f"  Iteration {i+1}: Total lookups = {lookup.lookup_count}")
    
    print("\nLookup counts per element:")
    for key, count in lookup.element_lookup_counts.items():
        print(f"  {key}: {count} lookups")
    
    print("\nAnalysis:")
    print(f"  - Root element lookup count: {lookup.element_lookup_counts.get('root', 0)}")
    print(f"  - Non-root elements have inconsistent caching")
    print(f"  - Total lookups: {lookup.lookup_count} (expected: 4 with perfect caching)")


if __name__ == "__main__":
    print("Demonstrating caching issue:\n")
    demonstrate_caching_issue()
    
    print("\n" + "="*60)
    print("Running property tests...")
    
    # Run a simple test case
    test_lookup_caching_property('<root><a/><b/></root>')
    print("Property test passed!")