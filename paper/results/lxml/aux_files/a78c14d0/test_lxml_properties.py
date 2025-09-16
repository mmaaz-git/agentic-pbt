import math
from hypothesis import assume, given, strategies as st, settings
import lxml.etree as etree
import lxml.html as html
import pytest

# Strategy for valid XML element names
xml_name = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_.-]*", fullmatch=True)

# Strategy for XML text content
xml_text = st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\x00<>&"), min_size=0)

# Strategy for attribute values
attr_value = st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\x00<>&\"'"), min_size=0)

@given(
    tag=xml_name,
    text=xml_text,
    attrs=st.dictionaries(xml_name, attr_value, min_size=0, max_size=5)
)
def test_xml_round_trip_simple(tag, text, attrs):
    """Test that fromstring(tostring(x)) preserves element structure"""
    elem = etree.Element(tag, attrib=attrs)
    elem.text = text if text else None
    
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert parsed.tag == elem.tag
    assert parsed.text == elem.text
    assert dict(parsed.attrib) == dict(elem.attrib)


@given(
    tag=xml_name,
    children=st.lists(
        st.tuples(xml_name, xml_text),
        min_size=0,
        max_size=10
    )
)
def test_xml_child_count_invariant(tag, children):
    """Test that number of children is preserved through serialization"""
    root = etree.Element(tag)
    for child_tag, child_text in children:
        child = etree.SubElement(root, child_tag)
        child.text = child_text if child_text else None
    
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert len(parsed) == len(root)
    assert len(list(parsed)) == len(children)


@given(text=xml_text)
def test_cdata_preserves_content(text):
    """Test that CDATA sections preserve their content exactly"""
    assume(text and "]]>" not in text)
    
    root = etree.Element("root")
    root.text = etree.CDATA(text)
    
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert parsed.text == text


@given(comment_text=st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\x00"), min_size=1))
def test_comment_round_trip(comment_text):
    """Test that comments preserve their content"""
    assume("-->" not in comment_text and "--" not in comment_text)
    
    root = etree.Element("root")
    comment = etree.Comment(comment_text)
    root.append(comment)
    
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert len(parsed) == 1
    assert parsed[0].tag == etree.Comment
    assert parsed[0].text == comment_text


@given(
    tag=xml_name,
    ns_prefix=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_.-]*", fullmatch=True),
    ns_uri=st.from_regex(r"http://[a-zA-Z0-9.-]+/[a-zA-Z0-9/]*", fullmatch=True)
)
def test_namespace_preservation(tag, ns_prefix, ns_uri):
    """Test that namespaces are preserved through serialization"""
    assume(ns_prefix != "xml" and ns_prefix != "xmlns")
    
    nsmap = {ns_prefix: ns_uri}
    qname = f"{{{ns_uri}}}{tag}"
    elem = etree.Element(qname, nsmap=nsmap)
    
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert parsed.tag == qname
    assert ns_uri in parsed.nsmap.values()


@given(
    xpath_expr=st.sampled_from([
        ".",
        "..",
        "*",
        "child::*",
        "descendant::*",
        "@*",
        "text()",
        "//",
    ])
)
def test_xpath_doesnt_crash(xpath_expr):
    """Test that basic XPath expressions don't crash on valid documents"""
    root = etree.Element("root")
    child = etree.SubElement(root, "child")
    child.text = "text"
    
    try:
        result = root.xpath(xpath_expr)
        assert result is not None
    except etree.XPathSyntaxError:
        pass


@given(
    pi_target=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_.-]*", fullmatch=True),
    pi_text=st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\x00?>"), min_size=0)
)
def test_processing_instruction_round_trip(pi_target, pi_text):
    """Test that processing instructions preserve their content"""
    assume(pi_target.lower() != "xml")
    
    root = etree.Element("root")
    pi = etree.PI(pi_target, pi_text)
    root.append(pi)
    
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert len(parsed) == 1
    assert parsed[0].tag == etree.PI
    assert parsed[0].target == pi_target
    if pi_text:
        assert parsed[0].text == pi_text or parsed[0].text == " " + pi_text


@given(
    tag=xml_name,
    tail_text=xml_text
)
def test_tail_text_preservation(tag, tail_text):
    """Test that tail text is preserved through serialization"""
    root = etree.Element("root")
    child = etree.SubElement(root, tag)
    child.tail = tail_text if tail_text else None
    
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert len(parsed) == 1
    assert parsed[0].tail == child.tail


@given(
    depth=st.integers(min_value=1, max_value=100),
    tag=xml_name
)
def test_deep_nesting_preservation(depth, tag):
    """Test that deeply nested structures are preserved"""
    root = etree.Element(tag)
    current = root
    for i in range(depth):
        current = etree.SubElement(current, f"{tag}{i}")
    
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Count depth
    count = 0
    current = parsed
    while len(current) > 0:
        count += 1
        current = current[0]
    
    assert count == depth


@given(
    html_str=st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\x00"), min_size=1)
)
def test_html_fragment_parsing_doesnt_crash(html_str):
    """Test that HTML fragment parsing handles arbitrary strings without crashing"""
    try:
        result = html.fragment_fromstring(html_str, create_parent='div')
        assert result is not None
    except (etree.ParserError, ValueError):
        pass


@given(
    attrs=st.dictionaries(
        xml_name,
        attr_value,
        min_size=1,
        max_size=10
    )
)
def test_attribute_order_independence(attrs):
    """Test that attribute order doesn't affect equality"""
    elem1 = etree.Element("root", attrib=attrs)
    elem2 = etree.Element("root", attrib=dict(reversed(attrs.items())))
    
    assert elem1.attrib == elem2.attrib
    assert set(elem1.attrib.items()) == set(elem2.attrib.items())


@given(
    text=st.text(min_size=1),
    encoding=st.sampled_from(['utf-8', 'utf-16', 'latin-1', 'ascii'])
)
def test_encoding_round_trip(text, encoding):
    """Test that different encodings preserve text content"""
    try:
        text.encode(encoding)
    except (UnicodeEncodeError, UnicodeDecodeError):
        assume(False)
    
    root = etree.Element("root")
    root.text = text
    
    try:
        xml_bytes = etree.tostring(root, encoding=encoding)
        parsed = etree.fromstring(xml_bytes)
        assert parsed.text == text
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass


@given(entity_name=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_.-]*", fullmatch=True))
def test_entity_reference_creation(entity_name):
    """Test that entity references can be created and used"""
    entity = etree.Entity(entity_name)
    assert entity.tag == etree.Entity
    assert entity.name == entity_name
    assert entity.text == f"&{entity_name};"


@given(
    xml_decl=st.booleans(),
    standalone=st.one_of(st.none(), st.booleans()),
    pretty_print=st.booleans()
)
def test_serialization_options_dont_affect_structure(xml_decl, standalone, pretty_print):
    """Test that serialization options don't change document structure"""
    root = etree.Element("root")
    child = etree.SubElement(root, "child")
    child.text = "text"
    
    xml_str = etree.tostring(
        root,
        encoding='unicode',
        xml_declaration=xml_decl,
        standalone=standalone,
        pretty_print=pretty_print
    )
    
    parsed = etree.fromstring(xml_str.encode('utf-8') if xml_decl else xml_str)
    
    assert parsed.tag == "root"
    assert len(parsed) == 1
    assert parsed[0].tag == "child"
    assert parsed[0].text == "text"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])