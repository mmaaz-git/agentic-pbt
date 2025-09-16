import lxml.etree as etree
from hypothesis import given, strategies as st, assume, settings
import string
import math

# Strategy for valid XML element names
def xml_name_strategy():
    first_char = st.one_of(
        st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')),
        st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')),
        st.just('_')
    )
    other_chars = st.text(
        alphabet=string.ascii_letters + string.digits + '._-',
        min_size=0,
        max_size=20
    )
    return st.builds(lambda f, o: f + o, first_char, other_chars)

# Strategy for XML text content
text_strategy = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cc', 'Cs'),
        blacklist_characters='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    ),
    max_size=100
)

# Strategy for attribute values
attr_value_strategy = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cc', 'Cs'),
        blacklist_characters='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    ),
    max_size=50
)

# Test 1: Round-trip property for simple elements
@given(
    tag=xml_name_strategy(),
    text=text_strategy,
    attr_name=xml_name_strategy(),
    attr_value=attr_value_strategy
)
@settings(max_examples=500)
def test_element_roundtrip(tag, text, attr_name, attr_value):
    # Create element
    elem = etree.Element(tag)
    if text:
        elem.text = text
    if attr_name and attr_value is not None:
        elem.set(attr_name, attr_value)
    
    # Serialize and parse back
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Check properties are preserved
    assert parsed.tag == elem.tag
    assert parsed.text == elem.text
    if attr_name and attr_value is not None:
        assert parsed.get(attr_name) == attr_value

# Test 2: tounicode vs tostring consistency
@given(
    tag=xml_name_strategy(),
    text=text_strategy
)
@settings(max_examples=300)
def test_tounicode_vs_tostring_consistency(tag, text):
    elem = etree.Element(tag)
    if text:
        elem.text = text
    
    unicode_result = etree.tounicode(elem)
    tostring_result = etree.tostring(elem, encoding='unicode')
    
    assert unicode_result == tostring_result

# Test 3: Element attribute manipulation invariants
@given(
    tag=xml_name_strategy(),
    attrs=st.dictionaries(
        xml_name_strategy(),
        attr_value_strategy,
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=300)
def test_element_attributes_invariants(tag, attrs):
    elem = etree.Element(tag)
    
    # Set all attributes
    for key, value in attrs.items():
        elem.set(key, value)
    
    # Check all attributes are set correctly
    for key, value in attrs.items():
        assert elem.get(key) == value
    
    # Check attribute count
    assert len(elem.attrib) == len(attrs)
    
    # Check keys match
    assert set(elem.attrib.keys()) == set(attrs.keys())

# Test 4: SubElement parent-child relationship
@given(
    parent_tag=xml_name_strategy(),
    child_tag=xml_name_strategy(),
    child_text=text_strategy
)
@settings(max_examples=300)
def test_subelement_parent_child_relationship(parent_tag, child_tag, child_text):
    parent = etree.Element(parent_tag)
    child = etree.SubElement(parent, child_tag)
    if child_text:
        child.text = child_text
    
    # Check parent-child relationship
    assert len(parent) == 1
    assert parent[0] is child
    assert child.getparent() is parent
    
    # Check serialization includes child
    xml_str = etree.tostring(parent, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    assert len(parsed) == 1
    assert parsed[0].tag == child_tag
    if child_text:
        assert parsed[0].text == child_text

# Test 5: Empty value handling
@given(tag=xml_name_strategy())
@settings(max_examples=200)
def test_empty_text_and_attribute_handling(tag):
    elem = etree.Element(tag)
    
    # Set empty text
    elem.text = ''
    assert elem.text == ''
    
    # Set empty attribute
    elem.set('empty', '')
    assert elem.get('empty') == ''
    
    # Serialize and parse back
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Empty text becomes None after parsing
    assert parsed.text is None
    # But empty attribute is preserved
    assert parsed.get('empty') == ''

# Test 6: Special character escaping in attributes
@given(
    tag=xml_name_strategy(),
    special_chars=st.text(alphabet='&<>"\'', min_size=1, max_size=10)
)
@settings(max_examples=300)
def test_special_character_escaping_attributes(tag, special_chars):
    elem = etree.Element(tag)
    elem.set('special', special_chars)
    
    # Serialize and parse back
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Special characters should be preserved
    assert parsed.get('special') == special_chars

# Test 7: Canonicalization idempotence
@given(
    tag=xml_name_strategy(),
    text=text_strategy,
    attrs=st.dictionaries(
        xml_name_strategy(),
        attr_value_strategy,
        min_size=0,
        max_size=5
    )
)
@settings(max_examples=200)
def test_canonicalize_idempotence(tag, text, attrs):
    elem = etree.Element(tag)
    if text:
        elem.text = text
    for key, value in attrs.items():
        elem.set(key, value)
    
    xml_str = etree.tostring(elem, encoding='unicode')
    
    # Canonicalize once
    canonical1 = etree.canonicalize(xml_str)
    
    # Canonicalize again - should be the same
    canonical2 = etree.canonicalize(canonical1)
    
    assert canonical1 == canonical2

# Test 8: Element iteration consistency
@given(
    parent_tag=xml_name_strategy(),
    child_tags=st.lists(xml_name_strategy(), min_size=1, max_size=10)
)
@settings(max_examples=200)
def test_element_iteration_consistency(parent_tag, child_tags):
    parent = etree.Element(parent_tag)
    
    # Create children
    children = []
    for tag in child_tags:
        child = etree.SubElement(parent, tag)
        children.append(child)
    
    # Test iteration
    assert len(parent) == len(child_tags)
    assert len(list(parent)) == len(child_tags)
    
    # Test indexing matches iteration
    for i, child in enumerate(parent):
        assert parent[i] is child
        assert child.tag == child_tags[i]

# Test 9: Namespace handling
@given(
    tag=xml_name_strategy(),
    prefix=st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
    uri=st.text(alphabet=string.ascii_letters + ':/._', min_size=1, max_size=30)
)
@settings(max_examples=200)
def test_namespace_handling(tag, prefix, uri):
    assume(prefix and uri)
    assume(':' not in prefix)
    
    nsmap = {prefix: uri}
    elem = etree.Element(tag, nsmap=nsmap)
    
    # Create a child with namespace
    child_tag = f'{{{uri}}}{tag}'
    child = etree.SubElement(elem, child_tag)
    
    # Serialize and parse
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Check namespace is preserved
    assert len(parsed) == 1
    assert parsed[0].tag == child_tag

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])