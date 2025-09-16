import html
import html.entities
from hypothesis import given, strategies as st, assume, settings
import sys


@given(st.integers(min_value=-sys.maxsize, max_value=sys.maxsize))
@settings(max_examples=1000)
def test_integer_overflow(num):
    """Test handling of very large integers in numeric entities"""
    entity = f'&#{num};'
    result = html.unescape(entity)
    
    # Should handle any integer without crashing
    assert isinstance(result, str)
    
    if num < 0:
        # Negative numbers should not be processed
        assert result == entity
    elif num > 0x10FFFF:
        # Numbers beyond Unicode range should be replacement character
        assert result == '\uFFFD'


@given(st.text(min_size=1, max_size=100))
def test_escape_idempotent(text):
    """Test that escape is idempotent when quote=False"""
    once = html.escape(text, quote=False)
    twice = html.escape(once, quote=False)
    
    # Escaping an already escaped string with quote=False should not change it
    assert once == twice


@given(st.sampled_from(list(html.entities.name2codepoint.keys())))
def test_all_name2codepoint_have_entitydefs(name):
    """Check that all entries in name2codepoint have corresponding entitydefs"""
    assert name in html.entities.entitydefs, f"{name} in name2codepoint but not in entitydefs"
    
    # Also check consistency
    codepoint = html.entities.name2codepoint[name]
    entity_char = html.entities.entitydefs[name]
    
    # entitydefs should contain the character corresponding to the codepoint
    if len(entity_char) == 1:
        assert ord(entity_char) == codepoint
    else:
        # Multi-character entitydefs should still decode to the right character
        expected = chr(codepoint) if codepoint <= 0x10FFFF else '\uFFFD'
        assert entity_char == expected


@given(st.sampled_from(list(html.entities.codepoint2name.keys())))
def test_all_codepoint2name_have_name2codepoint(codepoint):
    """Check reverse mapping consistency"""
    name = html.entities.codepoint2name[codepoint]
    assert name in html.entities.name2codepoint
    assert html.entities.name2codepoint[name] == codepoint


@given(st.text(alphabet=st.characters(min_codepoint=1, max_codepoint=0x10ffff), 
               min_size=0, max_size=50))
def test_escape_empty_and_none(text):
    """Test edge cases with escape"""
    # Empty string
    assert html.escape('') == ''
    assert html.unescape('') == ''
    
    # The actual test with generated text
    if text:
        escaped = html.escape(text)
        assert isinstance(escaped, str)
        assert len(escaped) >= len(text)  # Escaping can only make it longer or same


@given(st.text())
@settings(max_examples=500)
def test_no_crash_on_any_input(text):
    """Fuzz test - ensure no crashes on any input"""
    try:
        escaped = html.escape(text)
        unescaped = html.unescape(text)
        
        # Should always return strings
        assert isinstance(escaped, str)
        assert isinstance(unescaped, str)
        
        # Round-trip should work for escaped text
        assert html.unescape(escaped) == text
    except (ValueError, OverflowError, MemoryError):
        # These are acceptable for extremely large or malformed inputs
        pass


def test_html5_dict_duplicates():
    """Check for any duplicate keys with different values in html5 dict"""
    seen_keys = {}
    for key, value in html.entities.html5.items():
        base_key = key.rstrip(';')
        if base_key in seen_keys and seen_keys[base_key] != value:
            print(f"Found inconsistency: {base_key} -> {seen_keys[base_key]} vs {key} -> {value}")
            assert False, f"Inconsistent values for {base_key}"
        seen_keys[base_key] = value


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])