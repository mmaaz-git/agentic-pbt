from hypothesis import given, strategies as st, assume, settings, example
from lxml import etree
from lxml.sax import ElementTreeContentHandler, ElementTreeProducer, saxify, SaxError
from xml.sax.handler import ContentHandler
import re


# Test for edge cases and potential bugs

# Test 1: Empty namespace URI - edge case
@given(local_name=st.text(min_size=1, max_size=20).filter(lambda s: s.isalpha()))
@example(local_name="test")
def test_empty_namespace_uri(local_name):
    """Test handling of empty namespace URIs"""
    handler = ElementTreeContentHandler()
    
    # Try with empty namespace URI
    handler.startPrefixMapping("ns", "")
    handler.startElementNS(("", local_name), f"ns:{local_name}", None)
    handler.endElementNS(("", local_name), f"ns:{local_name}")
    handler.endPrefixMapping("ns")
    
    result = handler.etree.getroot()
    # Empty namespace should be treated specially
    assert result is not None


# Test 2: Mismatched element closing
@given(
    name1=st.text(min_size=1, max_size=10).filter(lambda s: s.isalpha()),
    name2=st.text(min_size=1, max_size=10).filter(lambda s: s.isalpha())
)
def test_mismatched_element_closing(name1, name2):
    """Test that mismatched element closing raises appropriate error"""
    assume(name1 != name2)
    
    handler = ElementTreeContentHandler()
    handler.startElementNS((None, name1), name1, None)
    
    try:
        handler.endElementNS((None, name2), name2)
        assert False, "Should have raised SaxError for mismatched elements"
    except SaxError as e:
        assert "Unexpected element closed" in str(e)
        assert name2 in str(e)


# Test 3: Namespace prefix without mapping
@given(
    prefix=st.text(min_size=1, max_size=5).filter(lambda s: s.isalpha()),
    local_name=st.text(min_size=1, max_size=10).filter(lambda s: s.isalpha())
)
def test_unmapped_prefix_ending(prefix, local_name):
    """Test ending a prefix mapping that was never started"""
    handler = ElementTreeContentHandler()
    
    # Try to end a prefix mapping that was never started
    try:
        handler.endPrefixMapping(prefix)
        # This might throw KeyError
    except KeyError:
        pass  # Expected behavior


# Test 4: Characters with no element
def test_characters_no_element():
    """Test adding characters when no element has been started"""
    handler = ElementTreeContentHandler()
    
    try:
        handler.characters("test text")
        # Should fail with IndexError or similar
        assert False, "Should fail when adding text with no element"
    except (IndexError, AttributeError):
        pass  # Expected


# Test 5: Complex namespace with special characters
@given(
    uri_suffix=st.text(
        alphabet=st.characters(min_codepoint=33, max_codepoint=126).filter(
            lambda c: c not in '<>&"\'{}'
        ),
        min_size=1,
        max_size=20
    )
)
def test_namespace_with_special_chars(uri_suffix):
    """Test namespace URIs with special characters"""
    ns_uri = f"http://example.com/ns/{uri_suffix}"
    
    root = etree.Element(f"{{{ns_uri}}}root")
    
    handler = ElementTreeContentHandler()
    saxify(root, handler)
    result = handler.etree.getroot()
    
    # Should preserve the namespace
    assert result.tag == f"{{{ns_uri}}}root"


# Test 6: Tail text handling edge case
@given(
    parent_text=st.text(min_size=0, max_size=50),
    child_tail=st.text(min_size=0, max_size=50)
)
def test_tail_text_handling(parent_text, child_tail):
    """Test proper handling of tail text"""
    handler = ElementTreeContentHandler()
    
    handler.startElementNS((None, "parent"), "parent", None)
    
    if parent_text:
        handler.characters(parent_text)
    
    handler.startElementNS((None, "child"), "child", None)
    handler.endElementNS((None, "child"), "child")
    
    if child_tail:
        handler.characters(child_tail)
    
    handler.endElementNS((None, "parent"), "parent")
    
    result = handler.etree.getroot()
    
    # Check tail is properly assigned
    if len(result) > 0 and child_tail:
        assert result[0].tail == child_tail


# Test 7: Processing instruction with empty data
@given(target=st.text(min_size=1, max_size=20).filter(lambda s: s.isalpha()))
def test_pi_empty_data(target):
    """Test processing instruction with empty data"""
    handler = ElementTreeContentHandler()
    
    # PI with empty data
    handler.processingInstruction(target, "")
    handler.startElementNS((None, "root"), "root", None)
    handler.endElementNS((None, "root"), "root")
    
    result = handler.etree.getroot()
    assert result.tag == "root"


# Test 8: Attribute with namespace collision
@given(
    local_name=st.text(min_size=1, max_size=10).filter(lambda s: s.isalpha()),
    value1=st.text(min_size=0, max_size=20),
    value2=st.text(min_size=0, max_size=20)
)
def test_attribute_namespace_collision(local_name, value1, value2):
    """Test attributes with same local name but different namespaces"""
    ns1 = "http://example.com/ns1"
    ns2 = "http://example.com/ns2"
    
    root = etree.Element("root")
    root.set(f"{{{ns1}}}{local_name}", value1)
    root.set(f"{{{ns2}}}{local_name}", value2)
    
    handler = ElementTreeContentHandler()
    saxify(root, handler)
    result = handler.etree.getroot()
    
    # Both attributes should be preserved
    assert result.get(f"{{{ns1}}}{local_name}") == value1
    assert result.get(f"{{{ns2}}}{local_name}") == value2


# Test 9: Deep nesting stress test
@given(depth=st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_deep_nesting(depth):
    """Test deeply nested elements"""
    handler = ElementTreeContentHandler()
    
    # Create deeply nested structure
    for i in range(depth):
        handler.startElementNS((None, f"level{i}"), f"level{i}", None)
    
    # Close all elements
    for i in range(depth - 1, -1, -1):
        handler.endElementNS((None, f"level{i}"), f"level{i}")
    
    result = handler.etree.getroot()
    
    # Check depth
    current = result
    for i in range(1, depth):
        assert len(current) == 1
        current = current[0]
        assert current.tag == f"level{i}"


# Test 10: None prefix handling
def test_none_prefix_handling():
    """Test explicit None prefix (default namespace)"""
    handler = ElementTreeContentHandler()
    
    # Use None as prefix for default namespace
    handler.startPrefixMapping(None, "http://example.com/default")
    
    handler.startElementNS((None, "root"), "root", None)
    handler.endElementNS((None, "root"), "root")
    
    handler.endPrefixMapping(None)
    
    result = handler.etree.getroot()
    # With default namespace, unqualified element should get the namespace
    assert result.tag == "{http://example.com/default}root"


# Test 11: Multiple text accumulation patterns
@given(
    texts=st.lists(st.text(min_size=0, max_size=10), min_size=1, max_size=10)
)
def test_multiple_text_accumulation(texts):
    """Test accumulating multiple text nodes"""
    handler = ElementTreeContentHandler()
    
    handler.startElementNS((None, "root"), "root", None)
    
    # Add multiple text pieces
    accumulated = ""
    for text in texts:
        handler.characters(text)
        accumulated += text
    
    handler.endElementNS((None, "root"), "root")
    
    result = handler.etree.getroot()
    
    # All text should be accumulated
    expected = accumulated if accumulated else None
    assert result.text == expected


# Test 12: Empty attributes dictionary vs None
def test_empty_attributes_handling():
    """Test difference between empty attributes dict and None"""
    handler1 = ElementTreeContentHandler()
    handler1.startElementNS((None, "root"), "root", {})
    handler1.endElementNS((None, "root"), "root")
    result1 = handler1.etree.getroot()
    
    handler2 = ElementTreeContentHandler()
    handler2.startElementNS((None, "root"), "root", None)
    handler2.endElementNS((None, "root"), "root")
    result2 = handler2.etree.getroot()
    
    # Both should produce same result
    assert etree.tostring(result1) == etree.tostring(result2)


# Test 13: SAX producer with element vs tree
@given(
    root_name=st.text(min_size=1, max_size=20).filter(lambda s: s.isalpha()),
    child_name=st.text(min_size=1, max_size=20).filter(lambda s: s.isalpha())
)
def test_producer_element_vs_tree(root_name, child_name):
    """Test ElementTreeProducer with element vs ElementTree"""
    # Create element
    root = etree.Element(root_name)
    child = etree.SubElement(root, child_name)
    
    # Test with element
    handler1 = ElementTreeContentHandler()
    producer1 = ElementTreeProducer(root, handler1)
    producer1.saxify()
    result1 = handler1.etree.getroot()
    
    # Test with tree
    tree = etree.ElementTree(root)
    handler2 = ElementTreeContentHandler()
    producer2 = ElementTreeProducer(tree, handler2)
    producer2.saxify()
    result2 = handler2.etree.getroot()
    
    # Should produce same result
    assert etree.tostring(result1) == etree.tostring(result2)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])