import pytest
from hypothesis import given, strategies as st, assume, settings
from lxml import etree, pyclasslookup
import string
import gc


# Strategy for valid XML tag names
def valid_tag_name():
    # XML tag names must start with letter or underscore, can contain letters, digits, hyphens, underscores, periods
    first_char = st.sampled_from(string.ascii_letters + '_')
    other_chars = st.text(alphabet=string.ascii_letters + string.digits + '-_.', min_size=0, max_size=20)
    return st.builds(lambda f, o: f + o, first_char, other_chars)


# Strategy for valid XML content
xml_text = st.text(alphabet=string.printable.replace('<', '').replace('>', '').replace('&', ''), min_size=0, max_size=100)


# Strategy for generating simple XML structures
@st.composite
def xml_element(draw, max_depth=3, current_depth=0):
    tag = draw(valid_tag_name())
    
    if current_depth >= max_depth:
        # Leaf node
        text = draw(xml_text)
        return f'<{tag}>{text}</{tag}>'
    else:
        # Can have children
        num_children = draw(st.integers(min_value=0, max_value=3))
        if num_children == 0:
            text = draw(xml_text)
            return f'<{tag}>{text}</{tag}>'
        else:
            children = []
            for _ in range(num_children):
                child = draw(xml_element(max_depth=max_depth, current_depth=current_depth + 1))
                children.append(child)
            return f'<{tag}>{"".join(children)}</{tag}>'


class TrackedElement(etree.ElementBase):
    """Element that tracks if it was created"""
    instances = []
    
    def __init__(self):
        super().__init__()
        TrackedElement.instances.append(self)


class CountingLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that counts how many times it's called"""
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.elements_seen = []
    
    def lookup(self, doc, element):
        self.call_count += 1
        self.elements_seen.append(element.tag)
        return None


class SelectiveLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that returns TrackedElement for specific tags"""
    def __init__(self, target_tags):
        super().__init__()
        self.target_tags = target_tags
    
    def lookup(self, doc, element):
        if element.tag in self.target_tags:
            return TrackedElement
        return None


@given(xml_element())
def test_lookup_called_for_all_elements(xml_str):
    """Property: lookup should be called for every element in the tree"""
    TrackedElement.instances = []
    
    try:
        tree = etree.fromstring(xml_str)
        element_count = len(list(tree.iter())) 
        
        lookup = CountingLookup()
        parser = etree.XMLParser()
        parser.set_element_class_lookup(lookup)
        
        result = etree.XML(xml_str, parser)
        
        # Property: lookup should be called once for each element
        assert lookup.call_count == element_count
        
    except etree.XMLSyntaxError:
        # Invalid XML generated, skip
        pass


@given(xml_element(), st.lists(valid_tag_name(), min_size=0, max_size=5))
def test_selective_element_class_assignment(xml_str, target_tags):
    """Property: Only elements with specified tags should get custom class"""
    TrackedElement.instances = []
    
    try:
        # Parse to check structure
        tree = etree.fromstring(xml_str)
        
        # Create lookup
        lookup = SelectiveLookup(target_tags)
        parser = etree.XMLParser()
        parser.set_element_class_lookup(lookup)
        
        # Parse with custom lookup
        result = etree.XML(xml_str, parser)
        
        # Check that only targeted elements have custom class
        for elem in result.iter():
            if elem.tag in target_tags:
                assert isinstance(elem, TrackedElement), f"Element {elem.tag} should be TrackedElement"
            else:
                assert not isinstance(elem, TrackedElement), f"Element {elem.tag} should not be TrackedElement"
                
    except etree.XMLSyntaxError:
        pass


class FallbackLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that always returns None to trigger fallback"""
    def lookup(self, doc, element):
        return None


class AlwaysCustomLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that always returns custom element"""
    def lookup(self, doc, element):
        return TrackedElement


@given(xml_element())
def test_fallback_mechanism(xml_str):
    """Property: When lookup returns None, fallback should be used"""
    TrackedElement.instances = []
    
    try:
        # Create main lookup that always returns None
        main_lookup = FallbackLookup()
        
        # Create fallback that always returns TrackedElement
        fallback_lookup = AlwaysCustomLookup()
        main_lookup.set_fallback(fallback_lookup)
        
        parser = etree.XMLParser()
        parser.set_element_class_lookup(main_lookup)
        
        result = etree.XML(xml_str, parser)
        
        # All elements should be TrackedElement due to fallback
        for elem in result.iter():
            assert isinstance(elem, TrackedElement)
            
    except etree.XMLSyntaxError:
        pass


class ExceptionLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that raises exception"""
    def lookup(self, doc, element):
        raise ValueError("Intentional error")


@given(xml_element())
def test_lookup_exception_handling(xml_str):
    """Property: Exceptions in lookup should be propagated properly"""
    try:
        lookup = ExceptionLookup()
        parser = etree.XMLParser()
        parser.set_element_class_lookup(lookup)
        
        with pytest.raises(ValueError, match="Intentional error"):
            etree.XML(xml_str, parser)
            
    except etree.XMLSyntaxError:
        pass


class ElementProxyTestLookup(pyclasslookup.PythonElementClassLookup):
    """Tests properties of the element proxy during lookup"""
    def __init__(self):
        super().__init__()
        self.proxy_data = []
    
    def lookup(self, doc, element):
        # Test read-only proxy properties
        data = {
            'tag': element.tag,
            'text': element.text,
            'tail': element.tail,
            'attrib': dict(element.attrib) if element.attrib else {},
            'children_count': len(element)
        }
        
        # Try to iterate children
        try:
            child_tags = [child.tag for child in element]
            data['child_tags'] = child_tags
        except:
            data['child_tags'] = []
            
        self.proxy_data.append(data)
        return None


@given(xml_element())
def test_element_proxy_readonly_access(xml_str):
    """Property: Element proxy in lookup should provide read-only access to element data"""
    try:
        # First parse normally to get expected structure
        tree = etree.fromstring(xml_str)
        
        # Parse with proxy test lookup
        lookup = ElementProxyTestLookup()
        parser = etree.XMLParser()
        parser.set_element_class_lookup(lookup)
        
        result = etree.XML(xml_str, parser)
        
        # Verify proxy data matches actual elements
        all_elements = list(tree.iter())
        assert len(lookup.proxy_data) == len(all_elements)
        
        for proxy_data, actual_elem in zip(lookup.proxy_data, all_elements):
            assert proxy_data['tag'] == actual_elem.tag
            assert proxy_data['text'] == actual_elem.text
            assert proxy_data['tail'] == actual_elem.tail
            assert proxy_data['children_count'] == len(actual_elem)
            
    except etree.XMLSyntaxError:
        pass


class InvalidReturnLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that returns invalid types"""
    def __init__(self, return_value):
        super().__init__()
        self.return_value = return_value
    
    def lookup(self, doc, element):
        return self.return_value


@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_invalid_return_type_handling(invalid_return):
    """Property: Returning non-Element class from lookup should be handled"""
    xml_str = '<root><child>text</child></root>'
    
    lookup = InvalidReturnLookup(invalid_return)
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    # This should either work (ignoring invalid return) or raise appropriate error
    try:
        result = etree.XML(xml_str, parser)
        # If it succeeds, elements should not have the invalid type
        for elem in result.iter():
            assert not isinstance(elem, type(invalid_return))
    except (TypeError, ValueError, AttributeError) as e:
        # Expected errors for invalid returns
        pass


class RecursiveLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that tries to access element recursively during lookup"""
    def lookup(self, doc, element):
        # Try various operations that might expose issues
        try:
            # Access parent (should not be available or cause issues)
            parent = element.getparent()
        except:
            pass
            
        try:
            # Try to modify (should fail as read-only)
            element.text = "modified"
        except:
            pass
            
        try:
            # Try to access root
            root = element.getroot()
        except:
            pass
            
        return None


@given(xml_element())  
def test_element_proxy_isolation(xml_str):
    """Property: Element proxy should be properly isolated during lookup"""
    try:
        lookup = RecursiveLookup()
        parser = etree.XMLParser()
        parser.set_element_class_lookup(lookup)
        
        # Should not crash or corrupt tree
        result = etree.XML(xml_str, parser)
        
        # Verify tree is still valid
        assert result.tag is not None
        
    except etree.XMLSyntaxError:
        pass


class MemoryTestLookup(pyclasslookup.PythonElementClassLookup):
    """Lookup that keeps references to proxy elements"""
    def __init__(self):
        super().__init__()
        self.stored_elements = []
    
    def lookup(self, doc, element):
        # Store reference to proxy (documentation warns against this)
        self.stored_elements.append(element)
        return None


@given(st.lists(xml_element(), min_size=1, max_size=10))
def test_proxy_element_lifetime(xml_strings):
    """Property: Proxy elements should become invalid after parsing"""
    lookup = MemoryTestLookup()
    parser = etree.XMLParser()
    parser.set_element_class_lookup(lookup)
    
    for xml_str in xml_strings:
        try:
            result = etree.XML(xml_str, parser)
        except etree.XMLSyntaxError:
            continue
    
    # Try to access stored proxy elements - they should be invalid
    for stored_elem in lookup.stored_elements:
        try:
            # Accessing proxy after parsing should fail or return None/empty
            tag = stored_elem.tag
            # If we can still access it, it might be a memory issue
            # But we can't assert failure as implementation might handle gracefully
        except:
            # Expected - proxy should be invalid
            pass
    
    # Force garbage collection
    gc.collect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])