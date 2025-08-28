import html
import html.entities
from hypothesis import given, strategies as st, assume, settings


@given(st.sampled_from(list(html.entities.name2codepoint.items())))
def test_name2codepoint_codepoint2name_inverse(name_codepoint_pair):
    name, codepoint = name_codepoint_pair
    if codepoint in html.entities.codepoint2name:
        reverse_name = html.entities.codepoint2name[codepoint]
        assert reverse_name == name, f"name2codepoint[{name!r}] = {codepoint}, but codepoint2name[{codepoint}] = {reverse_name!r}"


@given(st.sampled_from(list(html.entities.codepoint2name.items())))
def test_codepoint2name_name2codepoint_inverse(codepoint_name_pair):
    codepoint, name = codepoint_name_pair
    if name in html.entities.name2codepoint:
        reverse_codepoint = html.entities.name2codepoint[name]
        assert reverse_codepoint == codepoint, f"codepoint2name[{codepoint}] = {name!r}, but name2codepoint[{name!r}] = {reverse_codepoint}"


@given(st.sampled_from(list(html.entities.name2codepoint.keys())))
def test_entitydefs_consistency(name):
    if name in html.entities.entitydefs:
        char = html.entities.entitydefs[name]
        codepoint = html.entities.name2codepoint[name]
        
        if len(char) == 1:
            assert ord(char) == codepoint, f"entitydefs[{name!r}] = {char!r} (ord={ord(char)}), but name2codepoint[{name!r}] = {codepoint}"
        else:
            expected_char = chr(codepoint)
            assert char == expected_char, f"entitydefs[{name!r}] = {char!r}, but chr(name2codepoint[{name!r}]) = {expected_char!r}"


@given(st.sampled_from(list(html.entities.name2codepoint.keys())))
def test_html5_contains_legacy_entities(name):
    assert name in html.entities.html5 or name + ';' in html.entities.html5, \
        f"Entity {name!r} from name2codepoint not found in html5 dict"


@given(st.text(alphabet=st.characters(min_codepoint=1, max_codepoint=0x10ffff), min_size=1, max_size=100))
@settings(max_examples=1000)
def test_escape_unescape_round_trip(text):
    assume('\x00' not in text)
    assume(all(0xD800 > ord(c) or ord(c) > 0xDFFF for c in text))
    
    escaped = html.escape(text, quote=True)
    unescaped = html.unescape(escaped)
    assert unescaped == text, f"Round-trip failed: {text!r} -> {escaped!r} -> {unescaped!r}"


@given(st.sampled_from(list(html.entities.html5.keys())))
def test_html5_entity_unescape(entity_name):
    entity_with_amp = '&' + entity_name
    if not entity_name.endswith(';'):
        entity_with_amp += ';'
    
    expected = html.entities.html5[entity_name]
    result = html.unescape(entity_with_amp)
    
    if entity_name.endswith(';'):
        assert result == expected, f"unescape('&{entity_name}') = {result!r}, expected {expected!r}"


@given(st.integers(min_value=1, max_value=0x10ffff))
def test_numeric_entity_unescape(codepoint):
    assume(0xD800 > codepoint or codepoint > 0xDFFF)
    
    decimal_entity = f'&#{codepoint};'
    hex_entity = f'&#x{codepoint:x};'
    hex_entity_upper = f'&#X{codepoint:X};'
    
    expected = chr(codepoint) if codepoint not in html._invalid_codepoints else ''
    if codepoint in html._invalid_charrefs:
        expected = html._invalid_charrefs[codepoint]
    
    decimal_result = html.unescape(decimal_entity)
    hex_result = html.unescape(hex_entity)
    hex_upper_result = html.unescape(hex_entity_upper)
    
    assert decimal_result == expected, f"unescape('{decimal_entity}') = {decimal_result!r}, expected {expected!r}"
    assert hex_result == expected, f"unescape('{hex_entity}') = {hex_result!r}, expected {expected!r}"
    assert hex_upper_result == expected, f"unescape('{hex_entity_upper}') = {hex_upper_result!r}, expected {expected!r}"


@given(st.sampled_from(list(html.entities.name2codepoint.keys())))
def test_all_mappings_consistent(name):
    codepoint = html.entities.name2codepoint[name]
    
    if codepoint in html.entities.codepoint2name:
        assert html.entities.codepoint2name[codepoint] == name
    
    if name in html.entities.entitydefs:
        char = html.entities.entitydefs[name]
        if len(char) == 1:
            assert ord(char) == codepoint
    
    assert name in html.entities.html5 or name + ';' in html.entities.html5


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])