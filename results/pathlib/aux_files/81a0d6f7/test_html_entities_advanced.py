import html
import html.entities
from hypothesis import given, strategies as st, assume, settings, note


@given(st.text(alphabet='&<>"\';', min_size=1, max_size=50))
def test_escape_special_chars_combinations(text):
    escaped = html.escape(text, quote=True)
    assert '&' not in escaped or escaped.count('&') == escaped.count('&amp;') + escaped.count('&lt;') + escaped.count('&gt;') + escaped.count('&quot;') + escaped.count('&#x27;')
    assert '<' not in escaped or all(c == ';' for c in escaped if escaped[escaped.index(c)-1:escaped.index(c)+1] == '<;')
    assert '>' not in escaped or all(c == ';' for c in escaped if escaped[escaped.index(c)-1:escaped.index(c)+1] == '>;')


@given(st.text(min_size=1, max_size=20))
def test_unescape_malformed_entities(text):
    malformed = '&' + text
    result = html.unescape(malformed)
    
    if text and not text[0].isspace() and text[0] not in '<&#;':
        if ';' in text:
            semicolon_pos = text.index(';')
            entity_name = text[:semicolon_pos]
            
            if entity_name in html.entities.html5:
                assert result == html.entities.html5[entity_name] + text[semicolon_pos+1:]
            elif entity_name + ';' in html.entities.html5:
                assert result == html.entities.html5[entity_name + ';'] + text[semicolon_pos+1:]
            else:
                for x in range(len(entity_name)-1, 1, -1):
                    if entity_name[:x] in html.entities.html5:
                        assert result == html.entities.html5[entity_name[:x]] + text[x:]
                        break
                else:
                    assert result == '&' + text


@given(st.integers(min_value=-1000, max_value=0x110000))
def test_numeric_entity_edge_cases(codepoint):
    decimal_entity = f'&#{codepoint};'
    
    result = html.unescape(decimal_entity)
    
    if codepoint < 0:
        assert result == decimal_entity
    elif codepoint == 0 or (0xD800 <= codepoint <= 0xDFFF) or codepoint > 0x10FFFF:
        assert result == '\uFFFD'
    elif codepoint in html._invalid_charrefs:
        assert result == html._invalid_charrefs[codepoint]
    elif codepoint in html._invalid_codepoints:
        assert result == ''
    else:
        assert result == chr(codepoint)


@given(st.text(alphabet=st.characters(min_codepoint=1, max_codepoint=127), min_size=1, max_size=10))
def test_multiple_escapes(text):
    once_escaped = html.escape(text, quote=True)
    twice_escaped = html.escape(once_escaped, quote=True)
    
    once_unescaped = html.unescape(twice_escaped)
    assert once_unescaped == once_escaped
    
    twice_unescaped = html.unescape(once_unescaped)
    assert twice_unescaped == text


@given(st.lists(st.sampled_from(list(html.entities.html5.keys())), min_size=1, max_size=5))
def test_consecutive_entities(entity_names):
    text = ''.join('&' + name + ('' if name.endswith(';') else ';') for name in entity_names)
    expected = ''.join(html.entities.html5[name] for name in entity_names)
    
    result = html.unescape(text)
    assert result == expected


@given(st.integers(min_value=0, max_value=0x10ffff))
def test_numeric_without_semicolon(codepoint):
    assume(0xD800 > codepoint or codepoint > 0xDFFF)
    
    decimal_entity = f'&#{codepoint}'
    hex_entity = f'&#x{codepoint:x}'
    
    decimal_result = html.unescape(decimal_entity)
    hex_result = html.unescape(hex_entity)
    
    if codepoint == 0:
        expected = '\uFFFD'
    elif codepoint in html._invalid_charrefs:
        expected = html._invalid_charrefs[codepoint]
    elif codepoint in html._invalid_codepoints:
        expected = ''
    else:
        expected = chr(codepoint)
    
    assert decimal_result == expected
    assert hex_result == expected


@given(st.text(alphabet='0123456789abcdefABCDEF', min_size=1, max_size=6))
def test_hex_entity_case_insensitive(hex_digits):
    try:
        codepoint = int(hex_digits, 16)
    except ValueError:
        return
    
    if codepoint > 0x10ffff:
        return
    
    lower_entity = f'&#x{hex_digits.lower()};'
    upper_entity = f'&#X{hex_digits.upper()};'
    mixed_entity = f'&#x{hex_digits};'
    
    lower_result = html.unescape(lower_entity)
    upper_result = html.unescape(upper_entity)
    mixed_result = html.unescape(mixed_entity)
    
    assert lower_result == upper_result == mixed_result


@given(st.sampled_from(list(html.entities.html5.keys())))
def test_html5_semicolon_variants(entity_name):
    if entity_name.endswith(';'):
        without_semicolon = entity_name[:-1]
        if without_semicolon in html.entities.html5:
            with_semicolon_value = html.entities.html5[entity_name]
            without_semicolon_value = html.entities.html5[without_semicolon]
            
            assert with_semicolon_value == without_semicolon_value, \
                f"Inconsistent values: html5[{entity_name!r}] = {with_semicolon_value!r}, html5[{without_semicolon!r}] = {without_semicolon_value!r}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])