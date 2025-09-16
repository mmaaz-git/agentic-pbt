import html
import math
import re
from hypothesis import given, strategies as st, assume, settings

@given(st.text())
def test_escape_unescape_round_trip(s):
    escaped = html.escape(s)
    unescaped = html.unescape(escaped)
    assert unescaped == s, f"Round-trip failed for {repr(s)}: got {repr(unescaped)}"

@given(st.text())
def test_escape_idempotence(s):
    once = html.escape(s)
    twice = html.escape(once)
    assert once == twice, f"escape not idempotent for {repr(s)}"

@given(st.text())
def test_unescape_idempotence(s):
    once = html.unescape(s)
    twice = html.unescape(once)
    assert once == twice, f"unescape not idempotent for {repr(s)}"

@given(st.text())
def test_escape_no_special_chars_with_quote_true(s):
    escaped = html.escape(s, quote=True)
    assert '<' not in escaped or '&lt;' in escaped
    assert '>' not in escaped or '&gt;' in escaped
    assert '&' not in escaped or escaped.count('&') == escaped.count('&amp;') + escaped.count('&lt;') + escaped.count('&gt;') + escaped.count('&quot;') + escaped.count('&#x27;')
    assert '"' not in escaped or '&quot;' in escaped
    assert "'" not in escaped or '&#x27;' in escaped

@given(st.text())
def test_escape_no_special_chars_with_quote_false(s):
    escaped = html.escape(s, quote=False)
    assert '<' not in escaped or '&lt;' in escaped
    assert '>' not in escaped or '&gt;' in escaped
    assert '&' not in escaped or escaped.count('&') == escaped.count('&amp;') + escaped.count('&lt;') + escaped.count('&gt;')

@given(st.text())
def test_escape_preserves_length_order(s):
    escaped = html.escape(s)
    assert len(escaped) >= len(s)

@given(st.text())
def test_escape_empty_string_special_case(s):
    if s == '':
        assert html.escape(s) == ''
        assert html.unescape(s) == ''

@given(st.text(alphabet=st.characters(blacklist_categories=('Cs',), min_codepoint=1)))
def test_escape_unescape_no_surrogates(s):
    escaped = html.escape(s)
    unescaped = html.unescape(escaped)
    assert unescaped == s

@given(st.text())
def test_double_escape_unescape(s):
    double_escaped = html.escape(html.escape(s))
    single_unescaped = html.unescape(double_escaped)
    double_unescaped = html.unescape(single_unescaped)
    
    expected_after_single = html.escape(s)
    assert single_unescaped == expected_after_single
    assert double_unescaped == s

@given(st.text(alphabet=st.sampled_from(['&', '<', '>', '"', "'", 'a', 'b', '1', ' '])))
def test_special_chars_focused(s):
    escaped = html.escape(s)
    unescaped = html.unescape(escaped)
    assert unescaped == s

@given(st.text())
def test_numeric_entities_roundtrip(s):
    manual_escaped = ""
    for c in s:
        manual_escaped += f"&#{ord(c)};"
    
    unescaped = html.unescape(manual_escaped)
    assert unescaped == s

@given(st.integers(min_value=0, max_value=0x10FFFF))
def test_numeric_entity_valid_range(codepoint):
    if 0xD800 <= codepoint <= 0xDFFF:
        entity = f"&#{codepoint};"
        result = html.unescape(entity)
        assert result == '\uFFFD'
    elif codepoint in [0x1, 0xb, 0xe, 0x7f, 0xfffe, 0xffff, 0x10fffe, 0x10ffff]:
        entity = f"&#{codepoint};"
        result = html.unescape(entity)
        assert result == ''
    elif codepoint == 0:
        entity = f"&#{codepoint};"
        result = html.unescape(entity)
        assert result == '\uFFFD'
    elif codepoint in [0x0d, 0x80, 0x95, 0x9d]:
        pass
    else:
        entity = f"&#{codepoint};"
        result = html.unescape(entity)
        expected = chr(codepoint) if codepoint <= 0x10FFFF else '\uFFFD'
        if result != expected and codepoint not in range(0x80, 0xa0):
            assert result == expected

@given(st.text(), st.booleans())
def test_escape_quote_parameter(s, quote):
    escaped = html.escape(s, quote=quote)
    if quote:
        assert '"' not in escaped or '&quot;' in escaped
        assert "'" not in escaped or '&#x27;' in escaped
    else:
        quote_count = s.count('"')
        apostrophe_count = s.count("'")
        assert escaped.count('"') == quote_count
        assert escaped.count("'") == apostrophe_count

@given(st.text(alphabet=st.characters(min_codepoint=0x10000, max_codepoint=0x10FFFF)))
def test_high_unicode_roundtrip(s):
    escaped = html.escape(s)
    unescaped = html.unescape(escaped)
    assert unescaped == s

@given(st.text())
@settings(max_examples=1000)
def test_unescape_preserves_non_entities(s):
    if '&' not in s:
        assert html.unescape(s) == s

@given(st.text(alphabet=st.sampled_from(['&', ';', '#', 'x', 'X', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'A', 'B', 'C', 'D', 'E', 'F'])))
def test_malformed_entities(s):
    result = html.unescape(s)
    assert isinstance(result, str)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])