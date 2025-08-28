import html
from hypothesis import given, strategies as st, assume, settings, example
import re

# Test if semicolon-less numeric entities at end of string work consistently
@given(st.text(), st.integers(min_value=33, max_value=126))
def test_numeric_entity_without_semicolon_at_end(prefix, codepoint):
    """Test numeric entities without semicolon at string end"""
    # Create entity without semicolon
    entity_dec = f'{prefix}&#{ codepoint}'
    entity_hex = f'{prefix}&#x{codepoint:x}'
    entity_hex_upper = f'{prefix}&#X{codepoint:X}'
    
    result_dec = html.unescape(entity_dec)
    result_hex = html.unescape(entity_hex)
    result_hex_upper = html.unescape(entity_hex_upper)
    
    # All should parse the entity the same way (without semicolon)
    expected = prefix + chr(codepoint)
    assert result_dec == expected
    assert result_hex == expected
    assert result_hex_upper == expected

# Test consistency with leading zeros
@given(st.integers(min_value=33, max_value=126))
def test_numeric_entity_leading_zeros(codepoint):
    """Test that leading zeros in numeric entities work correctly"""
    # Test with various amounts of leading zeros
    variants = [
        f'&#{codepoint};',
        f'&#0{codepoint};',
        f'&#00{codepoint};',
        f'&#000{codepoint};',
        f'&#0000{codepoint};',
    ]
    
    expected = chr(codepoint)
    for variant in variants:
        result = html.unescape(variant)
        assert result == expected, f"Failed for {variant}"

# Test the regex behavior with tabs/newlines/formfeeds in entity names
def test_entity_name_forbidden_chars():
    """Test that certain characters are not allowed in entity names"""
    # According to regex: [^\t\n\f <&#;]{1,32}
    # These chars should terminate entity name matching
    
    # Tab should not be part of entity name
    assert html.unescape('&am\tp;') == '&am\tp;'  # Not recognized
    assert html.unescape('&\tamp;') == '&\tamp;'  # Not recognized
    
    # Newline should not be part of entity name
    assert html.unescape('&am\np;') == '&am\np;'  # Not recognized
    
    # Form feed should not be part of entity name
    assert html.unescape('&am\fp;') == '&am\fp;'  # Not recognized
    
    # Space should not be part of entity name
    assert html.unescape('&am p;') == '&am p;'  # Not recognized
    
    # < should not be part of entity name
    assert html.unescape('&am<p;') == '&am<p;'  # Not recognized
    
    # Another & should not be part of entity name
    assert html.unescape('&am&p;') == '&am&p;'  # Not recognized
    
    # # should not be part of entity name
    assert html.unescape('&am#p;') == '&am#p;'  # Not recognized

# Test for issues with multiple semicolons
@given(st.text(alphabet='0123456789'))
def test_multiple_semicolons_in_numeric(digits):
    """Test numeric entities with multiple semicolons"""
    assume(len(digits) > 0 and len(digits) < 10)
    
    # Multiple semicolons at end
    entity = f'&#{digits};;'
    result = html.unescape(entity)
    
    # Should parse the first semicolon as entity end
    num = int(digits)
    if num > 0x10FFFF:
        expected = '\uFFFD' + ';'
    elif 0xD800 <= num <= 0xDFFF:
        expected = '\uFFFD' + ';'
    elif num in [0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0xb, 0xe, 0xf, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x7f, 0xfffe, 0xffff, 0x10fffe, 0x10ffff]:
        if num == 0:
            expected = '\uFFFD' + ';'
        else:
            expected = '' + ';'
    elif num == 0:
        expected = '\uFFFD' + ';'
    elif num == 0xd:
        expected = '\r' + ';'
    elif num in [0x80, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8a, 0x8b, 0x8c, 0x8e, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9a, 0x9b, 0x9c, 0x9e, 0x9f]:
        # These have special replacements, skip detailed check
        return
    else:
        expected = chr(num) + ';'
    
    assert result == expected

# Test partial entity matching with very similar entity names
def test_similar_entity_names():
    """Test HTML5 partial matching with similar entity names"""
    # Test cases from HTML5 spec where partial matching matters
    
    # 'not' is an entity, but 'no' is not
    assert html.unescape('&not') == '¬'
    assert html.unescape('&no') == '&no'
    assert html.unescape('&not;') == '¬'
    
    # 'notin' should match 'not' + 'in'
    assert html.unescape('&notin') == '¬in'
    assert html.unescape('&notin;') == '∉'
    
    # Test the partial matching rule more thoroughly
    assert html.unescape('&notinva') == '¬inva'  # Matches 'not'
    assert html.unescape('&notinE') == '∉̸'  # Should match 'notinE'

# Test very specific edge case with regex backtracking
@given(st.text(alphabet='&'))
def test_many_ampersands(ampersands):
    """Test performance/correctness with many consecutive ampersands"""
    assume(len(ampersands) > 0 and len(ampersands) < 1000)
    
    # Many ampersands should not cause issues
    result = html.unescape(ampersands)
    assert result == ampersands  # No valid entities, should be unchanged

# Look for issues with escape order of operations
def test_escape_order_of_operations():
    """Test that escape replaces & first (as per comment in code)"""
    # The comment says & must be done first
    test_cases = [
        ('&<>"\'', '&amp;&lt;&gt;&quot;&#x27;'),
        ('<&', '&lt;&amp;'),
        ('>&', '&gt;&amp;'),
        ('"&', '&quot;&amp;'),
        ('\'&', '&#x27;&amp;'),
        ('&amp;', '&amp;amp;'),  # Double escape of &
        ('&lt;', '&amp;lt;'),    # & in entity gets escaped
    ]
    
    for input_str, expected in test_cases:
        result = html.escape(input_str)
        assert result == expected, f"Failed for {repr(input_str)}: got {repr(result)}, expected {repr(expected)}"

# Test the longest matching rule for partial entities  
def test_longest_match_rule():
    """Test that longest matching entity is used (HTML5 spec)"""
    # From the source code comment: "find the longest matching name"
    
    # If we have overlapping entities, longest should win
    # Let's find some examples in the html5 entities
    
    # 'not' exists, 'notin' exists - test the boundary
    assert html.unescape('&noti') == '¬i'  # Uses 'not'
    assert html.unescape('&notin') == '¬in'  # Uses 'not' because no semicolon
    assert html.unescape('&notin;') == '∉'  # Uses 'notin' with semicolon

# Test integer overflow protection
def test_huge_numeric_entity():
    """Test that extremely large numbers are handled correctly"""
    # Python handles arbitrary precision, but let's test the logic
    huge_nums = [
        10**20,
        10**50,
        10**100,
        2**63,  # Larger than typical int64
        2**100,
    ]
    
    for num in huge_nums:
        entity = f'&#{num};'
        result = html.unescape(entity)
        # All should be out of Unicode range, return replacement char
        assert result == '\uFFFD', f"Failed for {num}"

# Test consistency between hex lowercase and uppercase
@given(st.text(alphabet='0123456789abcdef', min_size=1, max_size=6))
def test_hex_case_consistency(hex_lower):
    """Test that hex entities work same in upper and lower case"""
    hex_upper = hex_lower.upper()
    
    entity_lower_x = f'&#x{hex_lower};'
    entity_upper_x = f'&#x{hex_upper};'
    entity_lower_X = f'&#X{hex_lower};'
    entity_upper_X = f'&#X{hex_upper};'
    
    result_lower_x = html.unescape(entity_lower_x)
    result_upper_x = html.unescape(entity_upper_x)
    result_lower_X = html.unescape(entity_lower_X)
    result_upper_X = html.unescape(entity_upper_X)
    
    # All four should give same result
    assert result_lower_x == result_upper_x == result_lower_X == result_upper_X

# Focused test on the rstrip(';') logic in _replace_charref
def test_rstrip_semicolon_behavior():
    """Test the rstrip(';') behavior in numeric parsing"""
    # The code does: int(s[2:].rstrip(';'), 16) for hex
    # and int(s[1:].rstrip(';')) for decimal
    
    # This means multiple trailing semicolons are stripped
    assert html.unescape('&#65;;;') == 'A;;'  # Only first ; is part of entity
    assert html.unescape('&#x41;;;') == 'A;;'
    
    # But semicolons in the middle should cause parse failure
    assert html.unescape('&#6;5;') == '\x06' + '5;'  # Parses &#6; leaves 5;

# Test interaction between escape and HTML comments/scripts
@given(st.text())
def test_escape_preserves_structure(text):
    """Ensure escape doesn't break HTML structure"""
    # Add HTML-like structure
    html_text = f'<div>{text}</div>'
    escaped = html.escape(html_text)
    
    # The < and > should be escaped
    assert '<div>' not in escaped
    assert '</div>' not in escaped
    assert '&lt;div&gt;' in escaped
    assert '&lt;/div&gt;' in escaped

# Edge case: Empty entity names
def test_empty_entity_names():
    """Test entities with empty names"""
    assert html.unescape('&;') == '&;'  # No entity name
    assert html.unescape('&#;') == '&#;'  # No number
    assert html.unescape('&#x;') == '&#x;'  # No hex digits
    assert html.unescape('&#X;') == '&#X;'  # No hex digits

# Test potential issue with quote parameter type checking
@given(st.text())
@example('')
@example('test')
@example('<>&"\'')
def test_quote_parameter_edge_cases(s):
    """Test quote parameter with unusual values"""
    # These should all work without raising exceptions
    
    # String values
    try:
        result1 = html.escape(s, quote='True')  # String 'True' is truthy
        result2 = html.escape(s, quote='False')  # String 'False' is truthy too!
        result3 = html.escape(s, quote='')  # Empty string is falsy
        
        # Non-empty strings are truthy in Python
        if '"' in s or "'" in s:
            assert '&quot;' in result1 or '&#x27;' in result1
            assert '&quot;' in result2 or '&#x27;' in result2  # 'False' is truthy!
            assert '&quot;' not in result3 and '&#x27;' not in result3
    except Exception as e:
        assert False, f"Unexpected exception with string quote values: {e}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])