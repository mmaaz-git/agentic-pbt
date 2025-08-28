import html
from hypothesis import given, strategies as st, settings


@given(st.integers(min_value=0, max_value=0xFFFF),
       st.text(alphabet='0123456789abcdefABCDEF', min_size=1, max_size=5))
@settings(max_examples=500)
def test_numeric_entity_unexpected_parsing(codepoint, suffix):
    """Test that numeric entities with alphanumeric suffixes behave unexpectedly"""
    
    # Create entities with the suffix that looks like it could be part of the number
    decimal_entity = f'&#{codepoint}{suffix};'
    hex_entity = f'&#x{codepoint:x}{suffix};'
    
    decimal_result = html.unescape(decimal_entity)
    hex_result = html.unescape(hex_entity)
    
    # For decimal entities, if suffix starts with a digit, it could be parsed as part of the number
    if suffix and suffix[0].isdigit():
        # The parser might consume some digits from suffix
        try:
            extended_num = int(str(codepoint) + suffix.lstrip('0123456789')[:10])
            if extended_num > 0x10FFFF:
                # Would result in replacement character
                pass
        except:
            pass
    
    # For hex entities, if suffix starts with a hex digit, similar issue
    if suffix and suffix[0] in '0123456789abcdefABCDEF':
        # Could be partially consumed
        pass
    
    # The key insight: Check if the result contains unexpected partial parsing
    # Example: &#0A; -> '�A;' where 0 is parsed and A; remains
    if codepoint == 0 and suffix.startswith('A'):
        assert decimal_result == '\uFFFDA;', f"Unexpected: &#0A; -> {decimal_result!r}"


def test_specific_problematic_cases():
    """Test specific cases that demonstrate the parsing issue"""
    
    # Case 1: &#0A; - looks like it could be hex 0x0A but is actually decimal 0 + "A;"
    result1 = html.unescape('&#0A;')
    # Current behavior: parses &#0 as U+0000 (replaced with U+FFFD), leaves "A;"
    assert result1 == '\uFFFDA;', f"Expected '\\uFFFDA;' but got {result1!r}"
    
    # Case 2: &#x0x; - looks malformed but is parsed as &#x0 + "x;"
    result2 = html.unescape('&#x0x;')
    assert result2 == '\uFFFDx;', f"Expected '\\uFFFDx;' but got {result2!r}"
    
    # Case 3: &#100text; - parses &#100 as 'd', leaves "text;"
    result3 = html.unescape('&#100text;')
    assert result3 == 'dtext;', f"Expected 'dtext;' but got {result3!r}"
    
    # This behavior might be confusing for users who expect:
    # - Either the whole entity to be valid and parsed
    # - Or the whole entity to be invalid and left as-is
    # Instead, we get partial parsing.
    
    # Is this a bug? It depends on the HTML5 spec interpretation.
    # The spec allows numeric references without semicolons, but this can lead to confusion.


if __name__ == "__main__":
    test_specific_problematic_cases()
    print("All specific test cases passed - demonstrating the unexpected parsing behavior")
    
    # Run property-based tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])