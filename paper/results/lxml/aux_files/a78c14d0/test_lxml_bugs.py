import lxml.etree as etree
import lxml.html as html
from hypothesis import given, strategies as st, assume, settings
import pytest


# Test for potential bug in empty value handling
@given(
    tag=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_.-]*", fullmatch=True),
    value=st.just("")
)
def test_empty_attribute_value_preservation(tag, value):
    """Test that empty attribute values are preserved correctly"""
    elem = etree.Element(tag)
    elem.set("attr", value)
    
    # Serialize and parse back
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # Check the attribute value
    assert "attr" in parsed.attrib
    assert parsed.get("attr") == value
    assert parsed.attrib["attr"] == value


@given(
    tag=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_.-]*", fullmatch=True),
    attrs=st.dictionaries(
        st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_.-]*", fullmatch=True),
        st.just(""),
        min_size=1,
        max_size=5
    )
)
def test_multiple_empty_attributes(tag, attrs):
    """Test multiple empty attribute values"""
    elem = etree.Element(tag, attrib=attrs)
    
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    assert len(parsed.attrib) == len(attrs)
    for key, value in attrs.items():
        assert key in parsed.attrib
        assert parsed.attrib[key] == value


@given(
    content=st.text(alphabet=st.characters(min_codepoint=0x20, max_codepoint=0x7E), min_size=0, max_size=100)
)
def test_html_text_node_handling(content):
    """Test HTML text node handling with various content"""
    html_str = f"<div>{content}</div>"
    
    try:
        parsed = html.fromstring(html_str)
        if parsed.text is None:
            assert content == ""
        else:
            assert parsed.text == content
    except etree.ParserError:
        pass


@given(
    tag=st.from_regex(r"[a-zA-Z][a-zA-Z0-9]*", fullmatch=True),
    empty_attrs=st.integers(min_value=1, max_value=10)
)
def test_empty_attribute_serialization_format(tag, empty_attrs):
    """Test how empty attributes are serialized"""
    elem = etree.Element(tag)
    for i in range(empty_attrs):
        elem.set(f"attr{i}", "")
    
    xml_str = etree.tostring(elem, encoding='unicode')
    
    # Empty attributes should be serialized as attr=""
    assert xml_str.count('=""') == empty_attrs
    
    # Parse back and verify
    parsed = etree.fromstring(xml_str)
    assert len(parsed.attrib) == empty_attrs
    for i in range(empty_attrs):
        assert parsed.get(f"attr{i}") == ""


@given(
    whitespace=st.sampled_from(["", " ", "  ", "\t", "\n", " \n ", "\t\n"])
)
def test_whitespace_only_text_preservation(whitespace):
    """Test preservation of whitespace-only text content"""
    elem = etree.Element("root")
    elem.text = whitespace
    
    xml_str = etree.tostring(elem, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    if whitespace == "":
        assert parsed.text is None
    else:
        assert parsed.text == whitespace


@given(
    prefix=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True),
    local=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)
)
def test_qname_with_empty_namespace(prefix, local):
    """Test QName behavior with empty namespace URI"""
    assume(prefix not in ["xml", "xmlns"])
    
    # Create element with empty namespace
    nsmap = {prefix: ""}
    try:
        elem = etree.Element(f"{prefix}:{local}", nsmap=nsmap)
        xml_str = etree.tostring(elem, encoding='unicode')
        parsed = etree.fromstring(xml_str)
        
        # The behavior with empty namespace URIs is interesting
        assert parsed.tag == f"{prefix}:{local}" or parsed.tag == local
    except (ValueError, etree.LxmlError):
        pass


@given(
    content=st.text(min_size=0, max_size=10)
)
def test_cdata_empty_handling(content):
    """Test CDATA section with empty or special content"""
    assume("]]>" not in content)
    
    root = etree.Element("root")
    root.text = etree.CDATA(content)
    
    xml_str = etree.tostring(root, encoding='unicode')
    parsed = etree.fromstring(xml_str)
    
    # CDATA content should be preserved exactly
    assert parsed.text == content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])