"""Property-based tests for lxml.html module"""

import lxml.html
from lxml import etree
from hypothesis import given, strategies as st, assume, settings


@given(st.text(min_size=1).filter(lambda x: x.strip()))
def test_fromstring_tostring_roundtrip_text_fragments(html_text):
    """Test that parsing and serializing text maintains the content"""
    assume('<' not in html_text and '>' not in html_text)
    
    wrapped = f'<div>{html_text}</div>'
    parsed = lxml.html.fromstring(wrapped)
    
    result = lxml.html.tostring(parsed, encoding='unicode', method='html')
    
    assert html_text in result, f"Lost text content: {html_text!r}"


@given(st.text(min_size=1).filter(lambda x: x.strip() and not x.startswith('<')))
def test_fragment_fromstring_with_plain_text(text):
    """Test that fragment_fromstring handles plain text correctly"""
    assume('<' not in text and '>' not in text)
    
    try:
        result = lxml.html.fragment_fromstring(text, create_parent=True)
        assert result is not None
        assert result.text == text or text in lxml.html.tostring(result, encoding='unicode')
    except etree.ParserError:
        pass


@given(st.text(min_size=0))
def test_empty_value_handling(value):
    """Test that empty or whitespace-only values are handled correctly"""
    if not value or not value.strip():
        try:
            result = lxml.html.fromstring(value)
            assert False, f"Should raise error for empty/whitespace input: {value!r}"
        except etree.ParserError:
            pass


@given(st.text())
def test_document_fromstring_with_empty_values(html):
    """Test document_fromstring with various empty inputs"""
    if not html or (isinstance(html, str) and not html.strip()):
        try:
            result = lxml.html.document_fromstring(html)
            assert False, f"Should raise error for empty input: {html!r}"
        except etree.ParserError as e:
            assert "Document is empty" in str(e)


@given(st.one_of(
    st.just(''),
    st.just(' '),
    st.just('\n'),
    st.just('\t'),
    st.just('   \n\t   '),
))
def test_empty_string_variations(empty_val):
    """Test various empty string inputs"""
    try:
        result = lxml.html.fromstring(empty_val)
        assert False, f"fromstring should raise error for: {empty_val!r}"
    except etree.ParserError:
        pass
    
    try:
        result = lxml.html.document_fromstring(empty_val)
        assert False, f"document_fromstring should raise error for: {empty_val!r}"
    except etree.ParserError as e:
        assert "Document is empty" in str(e)


@given(st.sampled_from(['<div></div>', '<span></span>', '<p></p>', '<a></a>']))
def test_fragment_single_element(html):
    """Test that fragment_fromstring correctly parses single elements"""
    result = lxml.html.fragment_fromstring(html)
    assert result is not None
    assert result.tag in ['div', 'span', 'p', 'a']
    
    serialized = lxml.html.tostring(result, encoding='unicode')
    assert result.tag in serialized


@given(st.integers(min_value=0, max_value=10))
def test_nested_div_roundtrip(depth):
    """Test deeply nested structures maintain their depth"""
    html = '<div>' * depth + 'content' + '</div>' * depth
    
    parsed = lxml.html.fromstring(html)
    result = lxml.html.tostring(parsed, encoding='unicode')
    
    assert 'content' in result
    if depth > 0:
        assert result.count('<div>') == depth
        assert result.count('</div>') == depth


@given(st.lists(st.sampled_from(['<p>text</p>', '<div>content</div>', '<span>data</span>']), min_size=2, max_size=5))
def test_multiple_elements_fragment_error(elements):
    """Test that fragment_fromstring raises error for multiple elements"""
    html = ''.join(elements)
    
    try:
        result = lxml.html.fragment_fromstring(html)
        assert False, "Should raise error for multiple elements"
    except etree.ParserError as e:
        assert "Multiple elements found" in str(e)


@given(st.text(alphabet=st.characters(whitelist_categories=('Zs', 'Cc')), min_size=1))
def test_whitespace_only_values(whitespace):
    """Test handling of whitespace-only strings"""
    try:
        result = lxml.html.fromstring(whitespace)
        assert False, f"Should raise error for whitespace-only: {whitespace!r}"
    except etree.ParserError:
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])