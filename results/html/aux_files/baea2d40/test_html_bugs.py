import html
from hypothesis import given, strategies as st, assume, settings, example

# Test if unescape handles mixed valid/invalid entities correctly
@given(st.text(alphabet=st.sampled_from(['&', 'a', 'm', 'p', ';', 'l', 't', 'g', 'q', 'u', 'o', '#', '3', '4', 'x', '2', '7'])))
def test_mixed_entity_parsing(s):
    result = html.unescape(s)
    assert isinstance(result, str)
    
# Test entity without semicolon at string boundaries
@given(st.text())
def test_entity_at_boundaries(s):
    # Test entities at the beginning without semicolon
    test1 = '&amp' + s
    result1 = html.unescape(test1)
    assert result1 == '&' + s
    
    # Test entities at the end without semicolon
    test2 = s + '&amp'
    result2 = html.unescape(test2)
    assert result2 == s + '&'

# Test HTML5 longest named entity edge cases
@given(st.text())
def test_partial_long_entities(prefix):
    # CounterClockwiseContourIntegral is the longest valid entity
    partial = '&CounterClockwiseContourIntegr' + prefix
    result = html.unescape(partial)
    # This should not be recognized as an entity
    assert '&' in result or result == partial

# Test numeric character references with very large numbers
@given(st.integers(min_value=0x110000, max_value=10**18))
def test_large_numeric_references(num):
    entity = f'&#{num};'
    result = html.unescape(entity)
    # Should return replacement character for out-of-range
    assert result == '\uFFFD'

# Test hex references with invalid characters after valid prefix
@given(st.text(alphabet='0123456789abcdefABCDEF'), st.text(alphabet='ghijklmnopqrstuvwxyzGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()'))
def test_hex_reference_invalid_suffix(valid_hex, invalid_suffix):
    assume(len(valid_hex) > 0)
    assume(len(invalid_suffix) > 0)
    entity = f'&#x{valid_hex}{invalid_suffix}'
    result = html.unescape(entity)
    # Should parse up to the first invalid character
    expected_num = int(valid_hex, 16)
    if expected_num > 0x10FFFF:
        assert result[0] == '\uFFFD'
    elif 0xD800 <= expected_num <= 0xDFFF:
        assert result[0] == '\uFFFD'
    # Check rest matches the invalid suffix

# Test edge case with ampersand followed by valid entity name without semicolon
@given(st.text())
def test_entity_name_without_semicolon_behavior(suffix):
    # Test the specific HTML5 behavior for entities without semicolons
    test = '&notit' + suffix
    result = html.unescape(test)
    # According to HTML5 spec and the test file, this should be '¬it' + suffix
    assert result == '¬it' + suffix

# Test if escape handles already escaped strings
@given(st.text())
def test_escape_already_escaped(s):
    # First escape
    escaped_once = html.escape(s)
    # Check if escaping an already escaped string causes issues
    escaped_twice = html.escape(escaped_once)
    # The & from entities should be escaped to &amp;
    for entity in ['&lt;', '&gt;', '&amp;', '&quot;', '&#x27;']:
        if entity in escaped_once:
            assert entity.replace('&', '&amp;') in escaped_twice

# Test surrogate pair handling in escape
@given(st.text())
def test_escape_preserves_all_chars(s):
    escaped = html.escape(s)
    unescaped = html.unescape(escaped)
    # Round-trip should preserve everything 
    assert unescaped == s

# Focus on testing the _replace_charref internal behavior indirectly
@given(st.text(alphabet='0123456789'))
def test_numeric_reference_without_hash(digits):
    # Entity without # after &
    entity = f'&{digits};'
    result = html.unescape(entity)
    # Should not be recognized as numeric entity
    assert result == entity

# Test mixed case hex references
@given(st.text(alphabet='0123456789abcdefABCDEF'))
def test_mixed_case_hex(hex_digits):
    assume(len(hex_digits) > 0 and len(hex_digits) <= 6)
    for prefix in ['&#x', '&#X']:
        entity = f'{prefix}{hex_digits};'
        result = html.unescape(entity)
        expected_num = int(hex_digits, 16)
        if expected_num > 0x10FFFF:
            assert result == '\uFFFD'
        elif 0xD800 <= expected_num <= 0xDFFF:
            assert result == '\uFFFD'
        elif expected_num in [0x0, 0x1, 0xb, 0xe, 0x7f, 0xfffe, 0xffff, 0x10fffe, 0x10ffff]:
            if expected_num == 0:
                assert result == '\uFFFD'
            else:
                assert result == ''
        elif expected_num in [0xd, 0x80, 0x95, 0x9d]:
            # Special replacements
            pass
        elif 0xe <= expected_num <= 0x1f:
            assert result == ''
        elif 0x7f <= expected_num <= 0x9f and expected_num != 0x7f:
            # Check for special replacements in _invalid_charrefs
            pass
        else:
            assert result == chr(expected_num)

# Test extremely long strings with entities
@given(st.integers(min_value=1, max_value=100))
def test_repeated_entities(count):
    # Create a string with many entities
    text = '&amp;' * count
    result = html.unescape(text)
    assert result == '&' * count
    
    # Test escape on repeated special chars
    text2 = '<>' * count
    escaped = html.escape(text2)
    assert escaped == '&lt;&gt;' * count

# Test entity recognition with embedded semicolons
def test_entity_with_embedded_semicolon():
    # From the test file example
    test = '&quot;quot;'
    result = html.unescape(test)
    assert result == '"quot;'

# Test the special HTML5 partial entity matching
def test_html5_partial_matching():
    # These are from the test file and HTML5 spec
    assert html.unescape('&notit') == '¬it'
    assert html.unescape('&notit;') == '¬it;'
    assert html.unescape('&notin') == '¬in'
    assert html.unescape('&notin;') == '∉'

# Now let's test for actual bugs - focus on edge cases not covered
@given(st.text(min_size=1))
def test_escape_with_none_type(s):
    # Test potential type confusion - this should work
    escaped = html.escape(s, quote=True)
    assert isinstance(escaped, str)
    escaped2 = html.escape(s, quote=False)
    assert isinstance(escaped2, str)

# Test potential integer overflow in numeric references
def test_extremely_large_numeric_reference():
    # Python handles big integers well, but let's test
    huge_num = 10**100
    entity = f'&#{huge_num};'
    result = html.unescape(entity)
    # Should handle gracefully as out of range
    assert result == '\uFFFD'

# Look for bugs in the quote parameter handling
@given(st.text())
def test_quote_parameter_type_coercion(s):
    # These should work with truthy/falsy values
    escaped1 = html.escape(s, quote=1)  # truthy
    escaped2 = html.escape(s, quote=0)  # falsy
    escaped3 = html.escape(s, quote='')  # falsy
    escaped4 = html.escape(s, quote='yes')  # truthy
    
    # Check they behave as expected
    if '"' in s:
        assert ('&quot;' in escaped1) and ('&quot;' not in escaped2)
        assert ('&quot;' not in escaped3) and ('&quot;' in escaped4)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])