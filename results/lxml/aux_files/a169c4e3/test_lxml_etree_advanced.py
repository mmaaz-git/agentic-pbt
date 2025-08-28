import lxml.etree as etree
from hypothesis import given, strategies as st, assume, settings, seed
import string

# More advanced property tests targeting edge cases

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

# Test: QName round-trip property
@given(
    localname=xml_name_strategy(),
    namespace=st.text(alphabet=string.ascii_letters + ':/._', min_size=1, max_size=50)
)
@settings(max_examples=500)
def test_qname_roundtrip(localname, namespace):
    assume('/' in namespace or ':' in namespace)  # Make it look like a URI
    assume(namespace not in [':', ' ', '::'])  # Known invalid URIs
    
    try:
        qname = etree.QName(namespace, localname)
        
        # Parse the text representation back
        text_repr = str(qname)
        
        # Create element with this QName
        elem = etree.Element(qname)
        
        # Check the element has the right namespace and localname
        assert elem.tag == text_repr
        
        # Parse from string and check consistency
        xml_str = etree.tostring(elem, encoding='unicode')
        parsed = etree.fromstring(xml_str)
        assert parsed.tag == elem.tag
        
    except (ValueError, TypeError):
        # Skip invalid namespace URIs
        pass

# Test: CDATA section handling
@given(
    data=st.text(
        alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        ),
        min_size=0,
        max_size=100
    )
)
@settings(max_examples=500)
def test_cdata_handling(data):
    # Skip if data contains the CDATA end sequence
    assume(']]>' not in data)
    
    root = etree.Element('root')
    root.text = data
    
    # Add CDATA section
    root.text = None
    cdata = etree.CDATA(data)
    root.text = cdata
    
    # Serialize and check
    xml_str = etree.tostring(root, encoding='unicode')
    
    # Parse back
    parsed = etree.fromstring(xml_str)
    
    # CDATA content should be preserved as text
    assert parsed.text == data

# Test: Comment handling
@given(
    comment_text=st.text(
        alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00-'
        ),
        min_size=0,
        max_size=100
    )
)
@settings(max_examples=500)
def test_comment_handling(comment_text):
    # Comments can't contain '--' or end with '-'
    assume('--' not in comment_text)
    assume(not comment_text.endswith('-'))
    
    root = etree.Element('root')
    comment = etree.Comment(comment_text)
    root.append(comment)
    
    # Serialize
    xml_str = etree.tostring(root, encoding='unicode')
    
    # Parse back
    parsed = etree.fromstring(xml_str)
    
    # Check comment is preserved
    assert len(parsed) == 1
    assert isinstance(parsed[0], etree._Comment)
    assert parsed[0].text == comment_text

# Test: Processing instruction handling
@given(
    target=xml_name_strategy(),
    data=st.text(
        alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00?'
        ),
        min_size=0,
        max_size=100
    )
)
@settings(max_examples=500)
def test_processing_instruction(target, data):
    # PI target can't be 'xml' (case-insensitive)
    assume(target.lower() != 'xml')
    # PI data can't contain '?>'
    assume('?>' not in data)
    
    root = etree.Element('root')
    pi = etree.PI(target, data)
    root.append(pi)
    
    # Serialize
    xml_str = etree.tostring(root, encoding='unicode')
    
    # Parse back
    parsed = etree.fromstring(xml_str)
    
    # Check PI is preserved
    assert len(parsed) == 1
    assert isinstance(parsed[0], etree._ProcessingInstruction)
    assert parsed[0].target == target
    if data:
        assert parsed[0].text == data
    else:
        assert parsed[0].text is None

# Test: Entity reference handling
@given(name=xml_name_strategy())
@settings(max_examples=300)
def test_entity_reference(name):
    root = etree.Element('root')
    entity = etree.Entity(name)
    
    # Get the string representation
    entity_str = str(entity)
    assert entity_str == f'&{name};'
    
    # Entities can be appended to elements
    root.append(entity)
    
    # Serialize with method='c14n' to see entities
    xml_str = etree.tostring(root, encoding='unicode', method='c14n')
    
    # The entity should appear in the output
    assert f'&{name};' in xml_str

# Test: Large tree structure
@given(
    depth=st.integers(min_value=1, max_value=10),
    width=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100)
def test_deep_tree_structure(depth, width):
    def build_tree(parent, current_depth):
        if current_depth >= depth:
            return
        for i in range(width):
            child = etree.SubElement(parent, f'level{current_depth}_child{i}')
            child.text = f'text_{current_depth}_{i}'
            build_tree(child, current_depth + 1)
    
    root = etree.Element('root')
    build_tree(root, 0)
    
    # Serialize and parse
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Count nodes in both trees
    def count_nodes(elem):
        return 1 + sum(count_nodes(child) for child in elem)
    
    original_count = count_nodes(root)
    parsed_count = count_nodes(parsed)
    
    assert original_count == parsed_count

# Test: Attribute order preservation (though XML doesn't guarantee it)
@given(
    attrs=st.dictionaries(
        xml_name_strategy(),
        st.text(alphabet=string.printable, min_size=0, max_size=20),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=300)
def test_attribute_manipulation(attrs):
    elem = etree.Element('test')
    
    # Set attributes
    for key, value in attrs.items():
        elem.set(key, value)
    
    # Remove and re-add first attribute
    if attrs:
        first_key = list(attrs.keys())[0]
        first_value = elem.get(first_key)
        del elem.attrib[first_key]
        assert elem.get(first_key) is None
        elem.set(first_key, first_value)
        assert elem.get(first_key) == first_value

# Test: Text and tail handling
@given(
    text=st.text(min_size=0, max_size=50),
    tail=st.text(min_size=0, max_size=50)
)
@settings(max_examples=300)
def test_text_and_tail_handling(text, tail):
    parent = etree.Element('parent')
    child = etree.SubElement(parent, 'child')
    
    child.text = text if text else None
    child.tail = tail if tail else None
    
    # Serialize and parse
    xml_str = etree.tostring(parent, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Check text and tail
    parsed_child = parsed[0]
    
    # Empty strings become None in parsing
    expected_text = text if text else None
    expected_tail = tail if tail else None
    
    assert parsed_child.text == expected_text
    assert parsed_child.tail == expected_tail

# Test: Unicode handling in tags and attributes
@given(
    unicode_text=st.text(
        alphabet=st.characters(min_codepoint=0x100, max_codepoint=0x1000),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=200)
def test_unicode_in_content(unicode_text):
    elem = etree.Element('test')
    elem.text = unicode_text
    elem.set('attr', unicode_text)
    
    # Serialize and parse
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert parsed.text == unicode_text
    assert parsed.get('attr') == unicode_text

if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])