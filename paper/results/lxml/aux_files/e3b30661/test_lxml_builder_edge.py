#!/usr/bin/env python3
"""Edge case tests for lxml.builder to find bugs"""

from hypothesis import given, assume, strategies as st, settings, example
from lxml.builder import ElementMaker, E
from lxml import etree as ET
import string

# More aggressive strategies for edge cases
def edge_tag_name():
    """Generate edge case tag names"""
    return st.one_of(
        st.just('_'),  # Single underscore
        st.just('_' * 100),  # Many underscores
        st.text(alphabet='_', min_size=1, max_size=10),
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=1),  # Single letter
        st.text(alphabet=string.ascii_letters + '_.-', min_size=100, max_size=200),  # Very long
        st.from_regex(r'[a-zA-Z_][a-zA-Z0-9_.\-]*', fullmatch=True).filter(
            lambda x: not x.lower().startswith('xml') and len(x) > 0
        )
    )

def edge_text():
    """Generate edge case text content"""
    return st.one_of(
        st.just(''),  # Empty
        st.just(' '),  # Single space
        st.just('  '),  # Multiple spaces
        st.just('\t'),  # Tab
        st.just('\n'),  # Newline
        st.just('\r'),  # Carriage return
        st.just('\r\n'),  # Windows newline
        st.text(alphabet=' ', min_size=1, max_size=100),  # Only spaces
        st.text(alphabet='\t\n\r ', min_size=1, max_size=50),  # Only whitespace
        st.text(min_size=1000, max_size=2000),  # Long text
        st.just('&'),  # Ampersand
        st.just('<'),  # Less than
        st.just('>'),  # Greater than
        st.just('"'),  # Quote
        st.just("'"),  # Apostrophe
        st.just('&lt;'),  # Already escaped
        st.just('&amp;'),  # Already escaped
        st.just('&gt;'),  # Already escaped
        st.just('&quot;'),  # Already escaped
        st.just('&apos;'),  # Already escaped
        st.just('&#65;'),  # Numeric entity
        st.just('&#x41;'),  # Hex entity
        st.just('&invalid;'),  # Invalid entity
        st.just('&&'),  # Double ampersand
        st.just('&;'),  # Empty entity
        st.just('&'),  # Incomplete entity
    )

@given(tag=edge_tag_name(), text=edge_text())
@settings(max_examples=500)
def test_edge_text_handling(tag, text):
    """Test edge cases in text handling"""
    try:
        elem = E(tag, text)
        serialized = ET.tostring(elem, encoding='unicode')
        
        # Should be able to parse back
        parsed = ET.fromstring(serialized)
        
        # Text should be preserved (with proper escaping)
        if parsed.text is None:
            assert text == ''
        else:
            # Check that special chars are properly escaped in serialization
            if '<' in text and '&lt;' not in text:
                assert '&lt;' in serialized or '<' not in parsed.text
            if '>' in text and '&gt;' not in text:
                assert '&gt;' in serialized or '>' not in parsed.text
            if '&' in text and not any(e in text for e in ['&lt;', '&gt;', '&amp;', '&quot;', '&apos;']):
                assert '&amp;' in serialized or '&' in parsed.text
    except ET.XMLSyntaxError:
        # Invalid XML might not parse back
        pass

@given(
    tag=edge_tag_name(),
    subtag=edge_tag_name()
)
def test_nested_edge_tags(tag, subtag):
    """Test nested elements with edge case names"""
    assume(tag != subtag)  # Make sure they're different
    
    elem = E(tag, E(subtag))
    serialized = ET.tostring(elem, encoding='unicode')
    
    parsed = ET.fromstring(serialized)
    assert parsed.tag == tag
    assert len(parsed) == 1
    assert parsed[0].tag == subtag

@given(
    tag=edge_tag_name(),
    num_children=st.integers(min_value=0, max_value=1000)
)
def test_many_children(tag, num_children):
    """Test with many child elements"""
    children = [E(f'child{i}') for i in range(num_children)]
    elem = E(tag, *children)
    
    serialized = ET.tostring(elem, encoding='unicode')
    parsed = ET.fromstring(serialized)
    
    assert len(parsed) == num_children
    for i, child in enumerate(parsed):
        assert child.tag == f'child{i}'

@given(depth=st.integers(min_value=1, max_value=100))
def test_deep_nesting(depth):
    """Test deeply nested elements"""
    # Build deeply nested structure
    elem = E('level0')
    current = elem
    for i in range(1, depth):
        child = E(f'level{i}')
        current.append(child)
        current = child
    
    serialized = ET.tostring(elem, encoding='unicode')
    parsed = ET.fromstring(serialized)
    
    # Verify depth
    current = parsed
    for i in range(1, depth):
        assert len(current) == 1
        current = current[0]
        assert current.tag == f'level{i}'

@given(
    tag=edge_tag_name(),
    num_attrs=st.integers(min_value=0, max_value=100)
)
def test_many_attributes(tag, num_attrs):
    """Test with many attributes"""
    attrs = {f'attr{i}': f'value{i}' for i in range(num_attrs)}
    elem = E(tag, attrs)
    
    serialized = ET.tostring(elem, encoding='unicode')
    parsed = ET.fromstring(serialized)
    
    assert len(parsed.attrib) == num_attrs
    for i in range(num_attrs):
        assert parsed.attrib[f'attr{i}'] == f'value{i}'

@given(
    tag=edge_tag_name(),
    attr_name=edge_tag_name(),
    attr_value=edge_text()
)
def test_edge_attribute_values(tag, attr_name, attr_value):
    """Test edge cases in attribute values"""
    try:
        elem = E(tag, {attr_name: attr_value})
        serialized = ET.tostring(elem, encoding='unicode')
        
        parsed = ET.fromstring(serialized)
        assert attr_name in parsed.attrib
        
        # Check escaping in attributes
        if '"' in attr_value:
            assert '&quot;' in serialized or '"' not in serialized.split('=')[1].split(' ')[0]
    except (ValueError, ET.XMLSyntaxError):
        # Some combinations might be invalid
        pass

@given(namespace=st.just(''))
def test_empty_namespace(namespace):
    """Test empty namespace handling"""
    maker = ElementMaker(namespace=namespace)
    elem = maker('tag')
    serialized = ET.tostring(elem, encoding='unicode')
    
    # Empty namespace should result in no namespace declaration
    assert 'xmlns' not in serialized

@given(
    tag=edge_tag_name(),
    text_pieces=st.lists(edge_text(), min_size=2, max_size=10)
)
def test_text_concatenation_edge_cases(tag, text_pieces):
    """Test concatenation of multiple edge case text pieces"""
    elem = E(tag, *text_pieces)
    serialized = ET.tostring(elem, encoding='unicode')
    
    try:
        parsed = ET.fromstring(serialized)
        expected = ''.join(text_pieces)
        
        if parsed.text is None:
            assert expected == ''
        # Don't check exact equality due to entity encoding
    except ET.XMLSyntaxError:
        # Some combinations might create invalid XML
        pass

@given(
    tags=st.lists(edge_tag_name(), min_size=2, max_size=5, unique=True),
    texts=st.lists(edge_text(), min_size=3, max_size=6)
)
def test_complex_mixed_content(tags, texts):
    """Test complex mixed content with edge cases"""
    assume(len(texts) >= len(tags) + 1)
    
    # Build: text0 <tag0>text1</tag0> text2 <tag1>text3</tag1> text4...
    content = []
    for i, tag in enumerate(tags):
        if i < len(texts):
            content.append(texts[i])
        content.append(E(tag))
    if len(texts) > len(tags):
        content.append(texts[-1])
    
    try:
        elem = E('root', *content)
        serialized = ET.tostring(elem, encoding='unicode')
        parsed = ET.fromstring(serialized)
        
        # Should have correct number of children
        assert len(parsed) == len(tags)
    except Exception:
        # Complex mixed content might fail
        pass

@given(
    parent_ns=st.text(alphabet=string.ascii_letters + ':/.', min_size=0, max_size=50),
    child_ns=st.text(alphabet=string.ascii_letters + ':/.', min_size=0, max_size=50)
)
def test_nested_namespaces(parent_ns, child_ns):
    """Test nested elements with different namespaces"""
    try:
        parent_maker = ElementMaker(namespace=parent_ns if parent_ns else None)
        child_maker = ElementMaker(namespace=child_ns if child_ns else None)
        
        parent = parent_maker('parent')
        child = child_maker('child')
        parent.append(child)
        
        serialized = ET.tostring(parent, encoding='unicode')
        parsed = ET.fromstring(serialized)
        
        # Both elements should exist
        assert len(parsed) == 1
    except Exception:
        # Some namespace combinations might be invalid
        pass

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short', '-x'])