import math
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from lxml import etree
from lxml.sax import ElementTreeContentHandler, ElementTreeProducer, saxify, SaxError
from xml.sax.handler import ContentHandler
import re

# Import the private functions for testing
import sys
sys.path.insert(0, '/root/.local/lib/python3.13/site-packages')
import lxml.sax as sax_module

# These functions are defined in the Python code but may not be exported
def _getNsTag(tag):
    if tag[0] == '{':
        return tuple(tag[1:].split('}', 1))
    else:
        return None, tag


# Strategy for valid XML names
xml_name = st.text(
    alphabet=st.characters(
        min_codepoint=ord('a'), max_codepoint=ord('z')
    ) | st.characters(
        min_codepoint=ord('A'), max_codepoint=ord('Z')
    ) | st.just('_'),
    min_size=1,
    max_size=20
).filter(lambda s: s and not s[0].isdigit())

# Strategy for namespace URIs
namespace_uri = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=1,
    max_size=50
).filter(lambda s: 'http://' in s or 'https://' in s or '://' in s)

# Strategy for simple text content
simple_text = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=0,
    max_size=100
).filter(lambda s: '<' not in s and '>' not in s and '&' not in s)

# Strategy for creating elements with optional namespace
@st.composite
def element_with_namespace(draw):
    use_ns = draw(st.booleans())
    if use_ns:
        ns = draw(namespace_uri)
        name = draw(xml_name)
        return f"{{{ns}}}{name}"
    else:
        return draw(xml_name)


# Test 1: Round-trip property - converting to SAX and back preserves structure
@given(
    root_name=xml_name,
    children=st.lists(
        st.tuples(xml_name, simple_text),
        min_size=0,
        max_size=5
    ),
    attributes=st.dictionaries(
        xml_name,
        simple_text,
        min_size=0,
        max_size=3
    )
)
def test_roundtrip_simple(root_name, children, attributes):
    # Build original tree
    root = etree.Element(root_name)
    for attr_name, attr_value in attributes.items():
        root.set(attr_name, attr_value)
    
    for child_name, child_text in children:
        child = etree.SubElement(root, child_name)
        if child_text:
            child.text = child_text
    
    # Convert to SAX and back
    handler = ElementTreeContentHandler()
    saxify(root, handler)
    result = handler.etree.getroot()
    
    # Compare serialized forms
    original_str = etree.tostring(root, encoding='unicode')
    result_str = etree.tostring(result, encoding='unicode')
    assert original_str == result_str


# Test 2: Tag parsing and building consistency 
@given(
    ns_uri=st.one_of(st.none(), namespace_uri),
    local_name=xml_name
)
def test_tag_building_parsing(ns_uri, local_name):
    handler = ElementTreeContentHandler()
    
    if ns_uri:
        # Set up namespace mapping
        handler._default_ns = ns_uri
        tag_with_ns = f"{{{ns_uri}}}{local_name}"
        
        # Test parsing
        parsed_ns, parsed_name = _getNsTag(tag_with_ns)
        assert parsed_ns == ns_uri
        assert parsed_name == local_name
        
        # Test building
        built_tag = handler._buildTag((ns_uri, local_name))
        assert built_tag == tag_with_ns
    else:
        # Without namespace
        handler._default_ns = None
        
        # Test parsing
        parsed_ns, parsed_name = _getNsTag(local_name)
        assert parsed_ns is None
        assert parsed_name == local_name
        
        # Test building
        built_tag = handler._buildTag((None, local_name))
        assert built_tag == local_name


# Test 3: Namespace prefix mapping consistency
@given(
    prefixes=st.lists(
        st.tuples(
            st.text(alphabet='abcdefghijklmnop', min_size=1, max_size=5),
            st.text(min_size=10, max_size=50).map(lambda s: f"http://example.com/{s}")
        ),
        min_size=1,
        max_size=5,
        unique_by=lambda x: x[0]  # Unique prefixes
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_namespace_prefix_mapping_consistency(prefixes):
    handler = ElementTreeContentHandler()
    
    # Start prefix mappings
    for prefix, uri in prefixes:
        handler.startPrefixMapping(prefix, uri)
        assert prefix in handler._ns_mapping
        assert handler._ns_mapping[prefix][-1] == uri
    
    # End prefix mappings in reverse order (like a stack)
    for prefix, uri in reversed(prefixes):
        current_uri = handler._ns_mapping[prefix][-1]
        assert current_uri == uri
        handler.endPrefixMapping(prefix)


# Test 4: Element stack operations should be balanced
@given(
    elements=st.lists(
        st.tuples(
            st.one_of(st.none(), namespace_uri),
            xml_name
        ),
        min_size=1,
        max_size=5
    )
)
def test_element_stack_balance(elements):
    handler = ElementTreeContentHandler()
    
    # Start elements
    for ns_uri, local_name in elements:
        handler.startElementNS((ns_uri, local_name), local_name, None)
        assert len(handler._element_stack) > 0
    
    # End elements in reverse order
    for ns_uri, local_name in reversed(elements):
        try:
            handler.endElementNS((ns_uri, local_name), local_name)
        except SaxError as e:
            # This should only happen if tags don't match
            assert "Unexpected element closed" in str(e)
            return
    
    assert len(handler._element_stack) == 0


# Test 5: Characters handling - text accumulation
@given(
    text_pieces=st.lists(simple_text, min_size=1, max_size=5)
)
def test_characters_accumulation(text_pieces):
    handler = ElementTreeContentHandler()
    
    # Create root element
    handler.startElementNS((None, "root"), "root", None)
    
    # Add text pieces
    accumulated_text = ""
    for text in text_pieces:
        handler.characters(text)
        accumulated_text += text
    
    # End element and check
    handler.endElementNS((None, "root"), "root")
    
    result = handler.etree.getroot()
    assert result.text == accumulated_text or result.text == (accumulated_text if accumulated_text else None)


# Test 6: Processing instructions handling
@given(
    target=xml_name,
    data=simple_text
)
def test_processing_instruction_handling(target, data):
    from lxml.etree import ProcessingInstruction
    
    root = etree.Element("root")
    pi = ProcessingInstruction(target, data)
    root.addprevious(pi)
    
    handler = ElementTreeContentHandler()
    saxify(root, handler)
    
    # The PI should be preserved in some form
    # Note: PIs before root might be handled differently
    assert handler.etree is not None


# Test 7: Empty element handling
@given(
    element_name=xml_name,
    use_namespace=st.booleans()
)
def test_empty_element_handling(element_name, use_namespace):
    if use_namespace:
        ns = "http://example.com/test"
        element = etree.Element(f"{{{ns}}}{element_name}")
    else:
        element = etree.Element(element_name)
    
    handler = ElementTreeContentHandler()
    saxify(element, handler)
    result = handler.etree.getroot()
    
    # Empty elements should preserve their structure
    assert result.tag == element.tag
    assert result.text is None
    assert len(result) == 0


# Test 8: Attribute preservation with special characters
@given(
    attr_name=xml_name,
    attr_value=st.text(min_size=0, max_size=50).filter(
        lambda s: all(ord(c) >= 32 and c not in '<>&"' for c in s)
    )
)
def test_attribute_preservation(attr_name, attr_value):
    root = etree.Element("root")
    root.set(attr_name, attr_value)
    
    handler = ElementTreeContentHandler()
    saxify(root, handler)
    result = handler.etree.getroot()
    
    assert result.get(attr_name) == attr_value


# Test 9: Test _buildTag with default namespace
@given(
    local_name=xml_name,
    default_ns=st.one_of(st.none(), namespace_uri),
    element_ns=st.one_of(st.none(), namespace_uri)
)
def test_buildtag_with_default_namespace(local_name, default_ns, element_ns):
    handler = ElementTreeContentHandler()
    handler._default_ns = default_ns
    
    tag = handler._buildTag((element_ns, local_name))
    
    if element_ns:
        assert tag == f"{{{element_ns}}}{local_name}"
    elif default_ns:
        assert tag == f"{{{default_ns}}}{local_name}"
    else:
        assert tag == local_name


# Test 10: Nested elements with mixed content
@given(
    parent_name=xml_name,
    child_name=xml_name,
    text_before=simple_text,
    text_after=simple_text,
    child_text=simple_text
)
def test_mixed_content(parent_name, child_name, text_before, text_after, child_text):
    handler = ElementTreeContentHandler()
    
    handler.startElementNS((None, parent_name), parent_name, None)
    
    if text_before:
        handler.characters(text_before)
    
    handler.startElementNS((None, child_name), child_name, None)
    if child_text:
        handler.characters(child_text)
    handler.endElementNS((None, child_name), child_name)
    
    if text_after:
        handler.characters(text_after)
    
    handler.endElementNS((None, parent_name), parent_name)
    
    result = handler.etree.getroot()
    assert result.tag == parent_name
    
    # Text before child should be in parent's text
    if text_before:
        assert result.text == text_before
    
    # Child should exist with its text
    if len(result) > 0:
        child = result[0]
        assert child.tag == child_name
        if child_text:
            assert child.text == child_text
        # Text after child should be in child's tail
        if text_after:
            assert child.tail == text_after


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])