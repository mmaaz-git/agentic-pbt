import html
import html.entities
from hypothesis import given, strategies as st, assume, settings, example


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20))
def test_partial_entity_matching(text):
    """Test the longest match behavior for partial entities"""
    entity = '&' + text
    result = html.unescape(entity)
    
    matches = []
    for i in range(len(text), 0, -1):
        prefix = text[:i]
        if prefix in html.entities.html5:
            matches.append((i, prefix, html.entities.html5[prefix]))
        if prefix + ';' in html.entities.html5:
            matches.append((i, prefix + ';', html.entities.html5[prefix + ';']))
    
    if matches:
        longest_match = max(matches, key=lambda x: x[0])
        if ';' in text and text.index(';') < longest_match[0]:
            pass
        else:
            if longest_match[1].endswith(';'):
                expected = longest_match[2] + text[longest_match[0]-1:]
            else:
                expected = longest_match[2] + text[longest_match[0]:]


@given(st.sampled_from(['&lt', '&gt', '&amp', '&quot', '&apos']))
def test_common_entities_without_semicolon(entity):
    """Test that common entities work without semicolon"""
    result = html.unescape(entity)
    
    expected_map = {
        '&lt': '<',
        '&gt': '>',
        '&amp': '&',
        '&quot': '"',
        '&apos': "'"
    }
    
    if entity in expected_map:
        assert result == expected_map[entity]


@given(st.integers(min_value=0x110000, max_value=0x200000))
def test_out_of_range_codepoints(codepoint):
    """Test codepoints beyond valid Unicode range"""
    decimal_entity = f'&#{codepoint};'
    hex_entity = f'&#x{codepoint:x};'
    
    decimal_result = html.unescape(decimal_entity)
    hex_result = html.unescape(hex_entity)
    
    assert decimal_result == '\uFFFD'
    assert hex_result == '\uFFFD'


@given(st.text(alphabet='&;', min_size=2, max_size=10))
def test_multiple_ampersands(text):
    """Test handling of multiple ampersands"""
    result = html.unescape(text)
    
    if '&;' in text:
        assert '&;' in result or '&' in result


@given(st.lists(st.integers(min_value=1, max_value=0x10ffff), min_size=1, max_size=5))
def test_mixed_numeric_entities(codepoints):
    """Test mixed decimal and hex entities"""
    entities = []
    expected = []
    
    for i, cp in enumerate(codepoints):
        if 0xD800 <= cp <= 0xDFFF:
            continue
            
        if i % 2 == 0:
            entities.append(f'&#{cp};')
        else:
            entities.append(f'&#x{cp:x};')
        
        if cp == 0:
            expected.append('\uFFFD')
        elif cp in html._invalid_charrefs:
            expected.append(html._invalid_charrefs[cp])
        elif cp in html._invalid_codepoints:
            expected.append('')
        elif cp > 0x10FFFF:
            expected.append('\uFFFD')
        else:
            expected.append(chr(cp))
    
    text = ''.join(entities)
    expected_text = ''.join(expected)
    
    result = html.unescape(text)
    assert result == expected_text


@given(st.text(min_size=1, max_size=10))
def test_entity_in_middle_of_text(entity_content):
    """Test entities embedded in normal text"""
    assume('&' not in entity_content and '<' not in entity_content and '>' not in entity_content)
    
    text = f"before &{entity_content}; after"
    result = html.unescape(text)
    
    if entity_content in html.entities.html5:
        expected = f"before {html.entities.html5[entity_content]} after"
        assert result == expected
    elif entity_content + ';' in html.entities.html5:
        expected = f"before {html.entities.html5[entity_content + ';']} after"
        assert result == expected
    elif entity_content.startswith('#'):
        try:
            if entity_content[1:].startswith('x') or entity_content[1:].startswith('X'):
                cp = int(entity_content[2:], 16)
            else:
                cp = int(entity_content[1:])
            
            if cp < 0 or cp > 0x10FFFF or (0xD800 <= cp <= 0xDFFF):
                pass
            elif cp == 0:
                expected = f"before \uFFFD after"
                assert result == expected
            elif cp in html._invalid_charrefs:
                expected = f"before {html._invalid_charrefs[cp]} after"
                assert result == expected
            elif cp in html._invalid_codepoints:
                expected = f"before  after"
                assert result == expected
            else:
                expected = f"before {chr(cp)} after"
                assert result == expected
        except (ValueError, OverflowError):
            pass


@given(st.sampled_from(list(html.entities.name2codepoint.keys())))
def test_case_sensitive_entity_names(entity_name):
    """Test that entity names are case-sensitive"""
    lower = '&' + entity_name.lower() + ';'
    upper = '&' + entity_name.upper() + ';'
    original = '&' + entity_name + ';'
    
    result_lower = html.unescape(lower)
    result_upper = html.unescape(upper)
    result_original = html.unescape(original)
    
    if entity_name != entity_name.lower() and entity_name.lower() not in html.entities.html5:
        assert result_lower == lower
    
    if entity_name != entity_name.upper() and entity_name.upper() not in html.entities.html5:
        assert result_upper == upper


@given(st.integers(min_value=0xD800, max_value=0xDFFF))
def test_surrogate_pairs(codepoint):
    """Test that surrogate pair codepoints are replaced with replacement character"""
    decimal_entity = f'&#{codepoint};'
    hex_entity = f'&#x{codepoint:x};'
    
    decimal_result = html.unescape(decimal_entity)
    hex_result = html.unescape(hex_entity)
    
    assert decimal_result == '\uFFFD'
    assert hex_result == '\uFFFD'


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])